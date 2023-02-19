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
from common import Course, Lectures, Slides, Video, Slice, CourseProviders, XMLHandler, link_join
import argparse
import os


class Scraper:
    SCROLL_PAUSE_TIME = 1.0
    COURSES_ON_ONE_SCROLL = 10  # The MIT website displays 10 more pages every time you scroll

    def __init__(self, num_courses, skip):
        # Initialise variables
        self.base_url = 'https://ocw.mit.edu/search/?f=Lecture%20Videos&f=Lecture%20Notes'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        service = Service('\chromedriver_win32\chromedriver.exe')
        self.driver = webdriver.Chrome(options=self.options, service=service)
        self.course_provider = CourseProviders.MIT
        self.skip_already_seen = skip
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
        self.driver.get(self.base_url)
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        num_courses = math.ceil(num_courses / self.COURSES_ON_ONE_SCROLL)
        print("======================\nLOADING {} COURSES\n====================".format(num_courses*self.COURSES_ON_ONE_SCROLL))

        for scroll_num in range(num_courses):
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
        #self.driver.quit()
        soup = BeautifulSoup(page, 'lxml')

        for course_card in soup.find_all('div', {'class': 'card-contents'}):
            # Course title info
            # Sometimes course title may not be loaded, so returns null type
            course_title_info = course_card.find('div', {'class': 'course-title'})
            try:
                course_title = course_title_info.find('span').string
            except AttributeError:
                    print("ERROR: Could not load course-title. Skipping...")
                    page = self.driver.page_source
                    #self.driver.quit()
                    soup = BeautifulSoup(page, 'lxml')
                    continue
            # Check if file already exists
            if self.skip_already_seen:
                dirname = os.path.dirname(__file__)
                fname = os.path.join(dirname, self.course_provider.name, "{}.xml".format(course_title[:20]))
                if os.path.isfile(fname):
                    print("Skipping course: {}, as it already exists".format(course_title[:20]))
                    continue
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

        # Get for course
        videos = self.get_single_course_videos(course_link)

        # Get content of each lecture (each PDF link for a course)
        lectures = Lectures()
        for i, (lecture_title, lecture_pdf_url, lecture_num) in enumerate(lec_num_to_link):
            # Get lecture slide content
            slides = self.get_pdf_data(lecture_pdf_url)
            # Get video content (assuming in same order as lecture slides)
            if videos:
                video = videos[i]
            else:
                video = None
            lectures.add_lecture(lecture_title, lecture_pdf_url, lecture_num, slides, (video))

        return lectures

    def get_lecture_notes(self, course_link):
        """ Get all of the lecture PDF links for a given course """
        service = Service('\chromedriver_win32\chromedriver.exe')
        driver = webdriver.Chrome(options=self.options, service=service)
        # Store the lecture number : lecture pdf link mapping
        lec_num_to_link = set()  # e.g {lec_title, lec_link, lec_num}

        pos_links = ['lecture-notes', 'lecture-summaries', 'lecture-slides', 'readings', 'lecture-notes']
        for i, pos_link in enumerate(pos_links):
            notes_link = link_join(course_link, 'pages', pos_link)
            
            driver.get(notes_link)
            page = driver.page_source
            soup = BeautifulSoup(page, 'lxml')
            # If page exists, break out of loop, we have a ready link to use
            if self.check_page_exists(soup):  # Sometimes endpoint works, but not what we expect
                break
            
        # If at final iteration and link still doesn't work (find hidden link)
        if not soup.find_all('tr'):
            # If table doesn't exist, but link does e.g https://ocw.mit.edu/courses/15-317-organizational-leadership-and-change-summer-2009/resources/lecture-notes/
            if self.check_page_exists(soup):
                try:
                    for i, lecture in enumerate(soup.find_all('div', {'class': 'pt-2'})):
                        lecture_num = str(i)
                        lecture_title = lecture.find('a', {'class': 'resource-list-title'}).text.strip('\n')
                        lecture_note_link = lecture.find('a', {'class': 'resource-list-title'})['href']

                        lecture_note_link = link_join('https://ocw.mit.edu', lecture_note_link)
                        lec_num_to_link.add((lecture_title, lecture_note_link, lecture_num))
                except AttributeError:
                    return
            else:
                return

        # Last ditch effort if table does not exist (download all PDFs on page)
        # e.g https://ocw.mit.edu/courses/15-433-investments-spring-2003/pages/lecture-notes/
        if not soup.find_all('tr'):
            lecture_num = 0
            for links in soup.find_all('a'):
                if 'PDF' in links.text.upper():
                    lecture_note_link = link_join('https://ocw.mit.edu', links.get('href'))
                    lecture_title = links.get('href').strip('/')
                    
                    lec_num_to_link.add((lecture_title, lecture_note_link, str(lecture_num)))
                    lecture_num += 1
        
        # If table exists
        for lecture in soup.find_all('tr'):
            if not lecture.find('td'):
                # Table did not load properly
                continue
            lecture_title = ""
            lecture_num = 0
            lecture_note_link = ""
            # Sometimes the first 'tr' might not be what we expect
            try:
                lecture_num = lecture.find('td', {'data-title': 'LEC\xa0#: '}).text.strip('\n')
                lecture_title = lecture.find('td', {'data-title': 'TOPICS: '}).text.strip('\n')
                lecture_note_link = lecture.find('td', {'data-title': 'LECTURE\xa0NOTES: '}).find('a')
            except AttributeError:
                lecture_num = lecture.find_all('td')[0].text.strip('\n')
                try:
                    if len(lecture.find_all('td')) == 4:
                        lecture_num = lecture.find_all('td')[0].text.strip('\n')
                        lecture_title = lecture.find_all('td')[1].text.strip('\n')
                        if 'PDF' in lecture_title.upper():
                            lecture_note_link = lecture.find_all('td')[1].find('a')
                        elif 'PDF' in lecture.find_all('td')[2].text.upper():
                            lecture_note_link = lecture.find_all('td')[2].find('a')
                        else:
                            lecture_note_link = lecture.find_all('td')[3].find('a')

                    if len(lecture.find_all('td')) == 3:
                        lecture_title = lecture.find_all('td')[1].text.strip('\n')
                        if 'PDF' in lecture_title.upper():  # e.g https://ocw.mit.edu/courses/20-310j-molecular-cellular-and-tissue-biomechanics-spring-2015/pages/lecture-slides/
                            lecture_note_link = lecture.find_all('td')[1].find('a')
                        else:
                            lecture_note_link = lecture.find_all('td')[2].find('a')

                    elif len(lecture.find_all('td')) == 2:
                        lecture_title = lecture.find_all('td')[1].find('a').text.strip('\n')
                        if lecture_title.upper() == 'PDF':  # e.g https://ocw.mit.edu/courses/21a-231j-gender-sexuality-and-society-spring-2006/pages/lecture-notes/
                            lecture_title = lecture.find_all('td')[1].text.strip('\n')
                        lecture_note_link = lecture.find_all('td')[1].find('a')

                    elif len(lecture.find_all('td')) == 1:  # e.g https://ocw.mit.edu/courses/21a-231j-gender-sexuality-and-society-spring-2006/pages/lecture-notes/
                        continue  # Likely not a lecture, but some sort of heading
                except AttributeError:
                    # Likely no lecture link
                    lecture_note_link = ""
            # Get response object for link
            try:
                lecture_note_link = lecture_note_link.get('href')
                # If link does not contain the subdomain - usually the case
                lecture_note_link = link_join('https://ocw.mit.edu', lecture_note_link)
            except Exception:
                print("Warning: No link found for lecture {}".format(lecture_num))
                continue
            lec_num_to_link.add((lecture_title, lecture_note_link, lecture_num))

        return lec_num_to_link

    def get_single_course_videos(self, course_link):
        """ Get data for videos for a lecture """
        service = Service('\chromedriver_win32\chromedriver.exe')
        driver = webdriver.Chrome(options=self.options, service=service)
        course_link = link_join(course_link, 'video_galleries', 'video-lectures')
        driver.get(course_link)
        page = driver.page_source
        soup = BeautifulSoup(page, 'lxml')
        # If page exists, break out of loop, we have a ready link to use
        if not self.check_page_exists(soup):  # Sometimes endpoint works, but not what we expect
            return
            
        videos = []

        for video in soup.find_all('a', {'class': 'video-link'}): # e.g https://ocw.mit.edu/courses/18-086-mathematical-methods-for-engineers-ii-spring-2006/video_galleries/video-lectures/
            video_link = link_join('https://ocw.mit.edu', video.get('href'))
            video_title = video.find('h5', {'class': 'video-title'}).text.strip('\n')
            video_link, slices = self.get_transcript(video_link)
            
            videos.append(Video(video_title, video_link, slices))

        return videos 

    def get_transcript(self, video_page):
        """ Given a single lecture video link, get the [Slices] """
        service = Service('\chromedriver_win32\chromedriver.exe')
        driver = webdriver.Chrome(options=self.options, service=service)
        driver.get(video_page)
        page = driver.page_source
        soup = BeautifulSoup(page, 'lxml')

        # If video is embedded, get the embedded link
        video_link = video_page
        # if soup.find('video'):
        #     video_link = soup.find('video').get('src').split('blob:')[1]

        slices = []
        for transcript in soup.find_all('div', {'class': 'transcript-line'}):
            timestamp = transcript.find('span', {'class': 'transcript-timestamp'}).text
            text = transcript.find('span', {'class': 'transcript-text'}).text
            slices.append(Slice(timestamp, text))

        return video_link, slices

    def get_pdf_data(self, pdf_url):
        """ Scrape textual information from a given lecture (PDF slide URL)
        Args:
            - pdf_link : Link to pdf file
        Returns:
            (Slides object) : The textual info in the PDF, broken into individual slides
        """
        # Requests URL and get response object
        if (not pdf_url) or (pdf_url == ""):
            return Slides()
        try:
            response = requests.get(pdf_url)
        except:
            return Slides()
        soup = BeautifulSoup(response.text, 'lxml')
        # Find all hyperlinks present on webpage
        link = soup.find('a', {'class': 'download-file'})
        if (not link) or link.get('href').split('.')[-1].lower() != 'pdf':
            print("ERROR: No PDF (link) found for this lecture, skipping...")
            return
        link = link_join('https://ocw.mit.edu', link.get('href'))
        response = requests.get(link)
        # Get the contents of PDF as text
        raw_data = response.content

        slides = Slides()
        with BytesIO(raw_data) as data:
            try:
                read_pdf = PyPDF2.PdfReader(data)
            except PyPDF2.errors.PdfReadError:
                print("ERROR: Could read PDF data for {}".format(link))
                return Slides()
            else:
                # Go through each slide in the lecture, and add it to Slides object
                for slide_num in range(len(read_pdf.pages)):
                    slides.insert_slide(slide_num, 
                    read_pdf.pages[slide_num].extract_text().encode('ascii', 'ignore').decode('ascii').strip())

        return slides


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--count', default=20, type=int)
    parser.add_argument('-s', '--skip', default=1, type=int)
    args = parser.parse_args()

    scraper = Scraper(args.count, args.skip)
