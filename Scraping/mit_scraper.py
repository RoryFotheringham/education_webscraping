import requests
import PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import xml.etree.cElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import math


""" XML Format 

doc = ET.Element("doc")
ET.SubElement(doc, "lectureno")
ET.SubElement(doc, "course")
ET.SubElement(doc, "date")
ET.SubElement(doc, "headline")
ET.SubElement(doc, "url")

slides = ET.SubElement(doc, "slides")
slide = ET.SubElement(slides, "slide")
ET.SubElement(slide, "slideno")
ET.SubElement(slide, "text")

ET.SubElement(doc, "source")

tree = ET.ElementTree(doc)
tree.write("index_format.xml")

"""

class Scraper:
    SCROLL_PAUSE_TIME = 1
    COURSES_ON_ONE_SCROLL = 10  # The MIT website displays 10 more pages every time you scroll

    def __init__(self, num_courses):
        # Initialise variables
        self.base_url = 'https://ocw.mit.edu/search/'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(chrome_options=self.options, executable_path='\chromedriver_win32\chromedriver.exe')
        self.driver.get(self.base_url)
        # Call methods
        self.scroll_scrape(num_courses)

    def scroll_scrape(self, num_courses):
        """ Scroll to the bottom of the page to load a specific number of courses to scrape
        Args:
            - num_courses: The number of courses to load
        """
        # Get scroll height
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")

        for scroll_num in range(math.ceil(num_courses / self.COURSES_ON_ONE_SCROLL) - 1):
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

            # Wait to load page
            time.sleep(self.SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        self.parse_main_page()

    def parse_main_page(self):
        """ Scrape the courses, now that we have scrolled to the bottom a few times to load the courses
        """
        page = self.driver.page_source
        self.driver.quit()
        soup = BeautifulSoup(page, 'html.parser')

        for link in soup.find_all('div', {'class': 'course-title'}):
            link_title = link.find('span')
            href = 'https://ocw.mit.edu' + link.find('a')['href']
            title = link_title.string
            self.get_single_course_data(href)

    def get_single_course_data(self, item_url):
        """ Scrape each individual course information
        """
        # TODO: Link to get_pdf_data etc..
        # source_code = requests.get(item_url)
        # soup = BeautifulSoup(source_code.text, 'html.parser')
        # # for item_description in soup.findAll('p'):
        # for item_description in soup.findAll('div', {'id': 'description'}):
        #     description = item_description.findAll('p')
        #     print(description[0].string)
    
    def get_pdf_data(self):
        """ Scrape textual information from PDF slides
        """
        url = "https://ocw.mit.edu/courses/6-s897-machine-learning-for-healthcare-spring-2019/resources/mit6_s897s19_lec1/"

        # Requests URL and get response object
        response = requests.get(url)
        # Parse text obtained
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all hyperlinks present on webpage
        links = soup.find_all('a')
        
        lec_num = 0
        # From all links check for pdf link and
        # if present download file
        for link in links:
            if ('.pdf' in link.get('href', [])):
                lec_num += 1
                print("Lectures Downloaded: {} ".format(lec_num))
        
                # Get response object for link
                try:
                    link_ref = link.get('href')
                    if link_ref[0] == '/':
                        link_ref = 'https://ocw.mit.edu{}'.format(link_ref)
                    response = requests.get(link_ref)
                except Exception as e:
                    print(e)
                    continue

                # Start building XML tree
                doc = ET.Element("doc")
                ET.SubElement(doc, "lectureno").text = str(lec_num)
                ET.SubElement(doc, "course").text = 'dummy'
                ET.SubElement(doc, "date").text = 'dummy'
                ET.SubElement(doc, "headline").text = 'dummy'
                ET.SubElement(doc, "url").text = link_ref
                slides = ET.SubElement(doc, "slides")
                
                # Get the contents of PDF as text
                raw_data = response.content
                with BytesIO(raw_data) as data:
                    read_pdf = PyPDF2.PdfReader(data)

                    slide = ET.SubElement(slides, "slide")
                    for page in range(len(read_pdf.pages)):
                        # Add slide info to XML tree
                        ET.SubElement(slide, "slideno").text = str(page)
                        ET.SubElement(slide, "text").text = read_pdf.pages[page].extract_text()
                
                ET.SubElement(doc, "source").text = 'dummy'
                tree = ET.ElementTree(doc)
                tree.write("lec_{}.xml".format(lec_num), encoding="utf-8")
        
        print("All PDF files text extracted")


if __name__ == '__main__':
    scraper = Scraper(30)