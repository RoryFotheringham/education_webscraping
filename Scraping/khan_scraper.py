import re
from urllib import response
import requests
import PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import xml.etree.cElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import math
import json
from common import *
from dynamic_transcript import Transcript_getter
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
        self.base_url = 'https://www.khanacademy.org'
        # Call methods
        self.parse_courses()


    def get_text_from_article(self, article_link):
        # currently this is painfully slow - there might be a quicker way to get the text than this
        
            response = requests.get(article_link)
            soup = BeautifulSoup(response.text, 'lxml')
            content = 'no content!'
            #print(str(soup.find_all('div')))
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                if '__PAGE_SETTINGS__' in script.string[:100]:
                    content = str(script.string)
                    for count, char in enumerate(content):  # the stuff in this loop doesn't work/do anything
                        if char == '{':                     # TODO get rid of this loop safely
                            content = content[count:]
                            break
                
                
            dict = ''
            tags = content.split('\n')
            for tag in tags:
                if '__PAGE_SETTINGS__' in tag:
                    dict = tag
                    
            if dict == '':
                return '' 
                    
            for count, char in enumerate(dict):
                if char == '{':
                    json_str = dict[count:]
                    break
            
            dict = json.loads(json_str[:-1])
            temp_key = '' 
            try:
                for key in dict['hydrate']['wbd'].keys():
                    if 'ContentForPath' in key:
                        temp_key = key
           
                if temp_key == '':
                    return ''
                                
                trans_content = dict['hydrate']['wbd'][temp_key]['data']['contentRoute']['listedPathData']['content']['translatedPerseusContent']
            
                trans_list = json.loads(trans_content)    
                
                text = ''
                for elem in trans_list:
                    text = text + ' ' + elem['content']
                    
            except KeyError:
                print('key error in article for {}'.format(article_link))
                return ''
                
            text = text.replace('\n', ' ')
            print('got article for {}'.format(article_link))
            return text 
                
                   
                   
    def get_transcript(self, link, trans_getter):
                
        return trans_getter.get_transcript(link)
                    
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
            
            contents = lesson_card.find('ul', {'class':'_37mhyh'})
            article_no = 0
            video_no = 0
            
            slides = Slides()
            videos = []
            trans_getter = Transcript_getter()
            
            activities = contents.find_all('li')
            for activity in activities:
                #time.sleep(2)
                is_article = activity.find('span', {'aria-label':'Article'}) # might be useful in future to consider 
                                                                                # aria-label:Talk-Through
                if is_article:
                    article_no += 1
                    activity_title = activity.find('span', {'class':'_14hvi6g8'}).text
                    article_link = self.base_url + activity.find('a')['href']
                    slides.insert_slide(str(article_no), self.get_text_from_article(article_link))
                    
                is_talkthrough = activity.find('span', {'aria-label':'Talk-through'})

                if is_talkthrough:
                    video_no += 1
                    activity_title = activity.find('span', {'class':'_14hvi6g8'}).text
                    activity_link = self.base_url + activity.find('a')['href']
                    videos.append(Video(activity_title, activity_link, self.get_transcript(activity_link, trans_getter)))
                    
                is_video = activity.find('span', {'aria-label':'Video'})
                    
                if is_video:
                    video_no += 1
                    activity_title = activity.find('span', {'class':'_14hvi6g8'}).text
                    activity_link = self.base_url + activity.find('a')['href']
                    videos.append(Video(activity_title, activity_link, self.get_transcript(activity_link, trans_getter)))
                    
            trans_getter.close()
            trans_getter.quit()
            course.lectures.add_lecture(lesson_card_title, link_join(self.base_url, lesson_link), str(lesson_no), slides, videos)
    
   


    def parse_khan_page(self, url):
    
        """_summary_ iterates through every 'course', adds a Course obj depth first
        and returns the course object
        """        
        

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        #print(str(soup)[:1000])
        #for link in soup.find_all('a', {'data-test-id':'lesson-link'}):
            #print(str(link['href']))

        for unit_card in soup.find_all('div', {'class':'_xmja1e8'}):
            unit_header = unit_card.find('a', {'data-test-id':'unit-header'})
            unit_title = unit_header.find('h3').text
            unit_link = unit_header['href']

            print('\n')          
            print(unit_title)
            print(unit_link)
            print('=============================')
            
            course = Course(unit_title, link_join(self.base_url, unit_link), ['None'], 'None')

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
                
    def parse_courses(self):
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, 'lxml')
        
        entries = soup.find_all('li', {'class':'_3hmsj'})
        links = []
        for entry in entries:
            link = entry.find('a')['href']
            if link != '/kids':
                links.append(link)

        for link in links:
            self.parse_khan_page(link_join(self.base_url, link))
        




if __name__ == '__main__':
    scraper = Scraper(30)