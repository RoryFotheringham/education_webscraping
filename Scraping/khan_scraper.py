import requests
import PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import xml.etree.cElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import math
from common import *
#from lecture import Lecture, Slide


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
    SCROLL_PAUSE_TIME = 0.8
    COURSES_ON_ONE_SCROLL = 10  # The MIT website displays 10 more pages every time you scroll

    def __init__(self, num_courses):
        # Initialise variables
        self.doc_list = []
        self.base_url = 'https://www.khanacademy.org/computing/computer-programming'
        # Call methods
        self.parse_khan_page()



    def get_text_from_article(self, article_link):
            response = requests.get(article_link)
            soup = BeautifulSoup(response.text, 'lxml')
            content = 'no content!'
            #print(str(soup.find_all('div')))
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                if '__PAGE_SETTINGS__' in script.string[:100]:
                    content = script.string[:20].strip()
                    
            return content # currently giving just raw javascript
                                        # so we can handle a string output
                                        # ultimately, this method should unpack the JS in 
                                        # content and return that
                
                   
                   
    def get_transcript(self, link):
        return 'transcript'
                    
    def get_lessons(self, course):
        """Retrieves all lessons, adds them to the course and passes
            down to the activities in each lesson

        Args:
            course(): a Course object
        """
        url = course.course_url
        unit_title = course.course_title
        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        course.add_lectures_info(Lectures())
        lesson_no = 0
        for lesson_card in soup.find_all('div', {'data-test-id':'lesson-card'}):
            lesson_no += 1
            lesson_card_title = lesson_card.find('a', {'data-test-id':'lesson-card-link'}).text
            lesson_link = lesson_card.find('a', {'data-test-id':'lesson-card-link'})['href']
            
            contents = lesson_card.find('div', {'class':'_1g8ypdt'})
            article_no = 0
            video_no = 0
            
            slides = Slides()
            videos = Videos()
            for activity in contents.find_all('div', {'class' : '_u7elqji'}):
                
                is_article = activity.find('span', {'aria-label':'Article'}) # might be useful in future to consider 
                                                                                # aria-label:Talk-Through
                if is_article:
                    article_no += 1
                    activity_title = activity.find('span', {'class':'_14hvi6g8'}).text
                    article_link = self.base_url + activity.find('a')['href']
                    slides.insert_slide(str(article_no, self.get_text_from_article(article_link)))
                    
                is_talkthrough = activity.find('span', {'aria-label':'Talk-through'})
                
                if is_talkthrough:
                    video_no += 1
                    activity_title = activity.find('span', {'class':'_14hvi6g8'}).text
                    activity_link = self.base_url + activity.find('a')['href']
                    videos.insert_slide(activity_title, activity_link, self.get_transcript(activity_link))
                    
            
            course.lectures.add_lecture(lesson_card_title, link_join(self.base_url, lesson_link), str(lesson_no), slides, videos)
    
   


    def parse_khan_page(self):
    
        """_summary_ iterates through every 'course', adds a Course obj depth first
        and returns the course object
        """        
        

        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, 'lxml')
        #print(str(soup)[:1000])
        #for link in soup.find_all('a', {'data-test-id':'lesson-link'}):
            #print(str(link['href']))


        for unit_card in soup.find_all('div', {'data-slug':'table-of-contents'}):
            unit_header = unit_card.find('a', {'data-test-id':'unit-header'})
            unit_title = unit_header.find('h3').text
            unit_link = unit_header['href']

            print('\n')          
            print(unit_title)
            print(unit_link)
            print('=============================')
            
            course = Course(unit_title, link_join(self.base_url, unit_link), 'None', 'None')

            self.get_lessons(course)
            print('got one!')

            handler = XMLHandler()
            handler.build_and_store_xml(CourseProviders(2), course)
            
            # docno = 0
            # for doc in self.doc_list:
            #     docno += 1
            #     tree = ET.ElementTree(doc)
            #     with open('khan_lec_{}.xml'.format(str(docno)), 'wb') as f:
            #         tree.write(f)                
                
            




if __name__ == '__main__':
    scraper = Scraper(30)