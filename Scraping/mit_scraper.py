import requests
import PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import xml.etree.cElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import math
from common import Course, Lectures, Slides, Videos, CourseProviders, XMLHandler, link_nav


class Scraper:
    SCROLL_PAUSE_TIME = 0.8
    COURSES_ON_ONE_SCROLL = 10  # The MIT website displays 10 more pages every time you scroll

    def __init__(self, num_courses):
        # Initialise variables
        self.base_url = 'https://ocw.mit.edu/search/'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        service = Service('\chromedriver_win32\chromedriver.exe')
        self.driver = webdriver.Chrome(options=self.options, service=service)
        self.driver.get(self.base_url)
        self.course_provider = CourseProviders.MIT
        # Call methods
        self.scroll_scrape(num_courses)

    def check_page_exists(self, soup):
        """ Check whether soup is using a dead url - specific to MIT website """
        if not soup:
            return False
        if soup.find('div', {'class': 'title-text m-auto h1 m-0'}):
            return 'page not found' not in soup.find('div', {'class': 'title-text m-auto h1 m-0'}).text.lower()
        else:
            return True

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
        """ Scrape the courses, now that we have scrolled to the bottom a few times to load the courses """
        page = self.driver.page_source
        self.driver.quit()
        soup = BeautifulSoup(page, 'lxml')

        for course_card in soup.find_all('div', {'class': 'card-contents'}):
            # Course title info
            # Sometimes course title may not be loaded, so returns null type
            try:
                course_title_info = course_card.find('div', {'class': 'course-title'})
            except AttributeError:
                time.sleep(0.2)
                course_title_info = course_card.find('div', {'class': 'course-title'})

            course_title = course_title_info.find('span').string
            course_url = 'https://ocw.mit.edu' + course_title_info.find('a')['href']
            # Course tags
            course_tag_info = course_card.find('div', {'class': 'topics-list'})
            course_tags = [tag.text for tag in course_tag_info.find_all('a', {'class': 'topic-link'})]
            # Grad / Undergrad
            level_info = course_card.find('div', {'class': ['lr-row', 'resource-header']}).text
            # Professor
            prof_info = course_card.find('div', {'class': ['lr-subtitle', 'listitem']}).find('a').text

            print("\nCourse: '{}'\nLink: {}\nTags: {}\nLevel: {}\nProf: {}\n".format(course_title, course_url, course_tags, level_info, prof_info))
            
            course = Course(course_title, course_url, course_tags, "28/01/2023")
            lectures = self.get_single_course_lectures(course_url)
            course.add_lectures_info(lectures)

            xml_handler = XMLHandler()
            xml_handler.build_and_store_xml(self.course_provider, course)

    def get_single_course_lectures(self, course_link):
        """ Gather all information for individual course by calling upon supporting methods """
        # Get all lecture PDF links for this course
        lec_num_to_link = self.get_lecture_notes(course_link)
        # Some lectures don't have PDF links
        if not lec_num_to_link:
            return

        # Get content of each lecture (each PDF link for a course)
        lectures = Lectures()
        for lecture_title, lecture_pdf_url, lecture_num in lec_num_to_link:
            slides = self.get_pdf_data(lec_link)
            lectures.add_lecture(lecture_title, lecture_pdf_url, lecture_num, slides, None)

        return lectures

    def get_lecture_notes(self, course_link):
        """ Get all of the lecture PDF links for a given course """
        notes_link = link_nav(course_link, 'pages', 'lecture-notes')

        service = Service('\chromedriver_win32\chromedriver.exe')
        driver = webdriver.Chrome(options=self.options, service=service)
        driver.get(notes_link)

        page = driver.page_source
        soup = BeautifulSoup(page, 'lxml')

        if not self.check_page_exists(soup):
            return
        # Store the lecture number : lecture pdf link mapping
        lec_num_to_link = set()  # e.g {lec_title, lec_link, lec_num}
        for lecture in soup.find_all('tr'):
            lecture_title = soup.find('td', {'data-title': 'TOPICS '}).text
            lecture_num = soup.find('td', {'data-title': 'LECTURE\xa0# '}).text
            lecture_note_link = soup.find('td', {'data-title': 'LECTURE\xa0NOTES: '}).find('a')
            # Get response object for link
            try:
                link_ref = lecture_note_link.get('href')
                # If link does not contain the subdomain - usually the case
                if link_ref[0] == '/':
                    link_ref = 'https://ocw.mit.edu{}'.format(link_ref)
            except Exception as e:
                print("Warning: No link found for this lecture")
                print(e)
                continue
            lec_num_to_link.add(lecture_title, lecture_note_link, lecture_num)
        
        return lec_num_to_link

    def get_pdf_data(self, pdf_url):
        """ Scrape textual information from a given lecture (PDF slide URL)
        Args:
            - pdf_link : Link to pdf file
        Returns:
            (Slides object) : The textual info in the PDF, broken into individual slides
        """
        # Requests URL and get response object
        response = requests.get(pdf_url)
        raw_data = response.content

        slides = Slides()
        with BytesIO(raw_data) as data:
            read_pdf = PyPDF2.PdfReader(data)
            # Go through each slide in the lecture, and add it to Slides object
            for slide_num in range(len(read_pdf.pages)):
                slides.insert_slide(slide_num, read_pdf.pages[slide_num].extract_text())

        return slides
        
        # tree = ET.ElementTree(doc)
        # tree.write("lec_{}.xml".format(lec_num), encoding="utf-8")


if __name__ == '__main__':
    scraper = Scraper(20)
