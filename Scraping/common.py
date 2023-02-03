from io import BytesIO
import xml.etree.cElementTree as ET
from lxml import etree
from lxml.builder import E
from enum import Enum
import os

class CourseProviders(Enum):
    """ Enumeration for course providers we are scraping """
    MIT = 1
    KHAN_ACADEMY = 2

def link_join(link, *args):
    """ Simplify navigating through links, this function allows you to go into deeper directories (specify in *args) """
    for arg in args:
        link += "{}{}".format("/" if (link[-1] != "/" and arg[0] != "/") else "", arg)
    return link


class Course:
    """ Handle the storage of a single course """
    def __init__(self, course_title, course_url, course_tags, date):
        self.course_title = course_title
        self.course_url = course_url
        self.course_tags = course_tags
        self.date = date
        self.lectures = None

    def add_lectures_info(self, lectures):
        self.lectures = lectures  # single instance of Lectures obj

    def get_info(self):
        return self.course_title, self.course_url, self.course_tags, self.date, self.lectures


class Lectures:
    """ Handle the storage of multiple lectures """
    def __init__(self):
        self.struct = set()  # {(lecture_title, lecture_pdf_url, lecture_num, slides, videos), ...}
    
    def add_lecture(self, lecture_title, lecture_pdf_url, lecture_num, slides, videos):
        self.struct.add((lecture_title, lecture_pdf_url, lecture_num, slides, videos))
    
    def get_info(self):
        return self.struct


class Slides:
    """ Handle the storage of multiple slides """
    def __init__(self):
        self.struct = set()  # {(slide_num, slide_text), ...}

    def insert_slide(self, slide_num, slide_text):
        self.struct.add((slide_num, slide_text))

    def get_info(self):
        return self.struct


class Videos:
    """ Handle the storage of multiple videos """
    def __init__(self):
        self.struct = set()  # {(video_title, video_url, transcript), ...}
    
    #def insert_slide(self, video_title, video_url, transcript: [Slice]):
    
    # PROBLEM WITH VIDEOS
    # we can't hash a list data type we need to get a different way to 
    # maybe self.struct can be a list rather than set?
    # i will investigate ...
    def insert_slide(self, video_title, video_url, transcript: list):
                                                                
        # Note: A 'transcript' is an array of Slices
        self.struct.add((video_title, video_url, transcript))
    
    def get_info(self):
        return self.struct


class Slice:
    """ Handle the storage of a single slice in the transcript """
    def __init__(self, time, text):
        self.time = time  # e.g: 28:40
        self.text = text  # e.g: So now, that's a picture with name but not details, right?
    def get_info(self):
        return (self.time, self.text)


class XMLHandler:
    """ Class to handle XML file creation and storage in desired structure for one whole course.
        Simply provide it with course_provider ENUM type and the Course class.
    """
    def __init__(self):
        self.course_title = None

    def build_and_store_xml(self, course_provider, course):
        def tag_func(course_tags):
            if not course_tags:
                return []
            return [E("list", a) for a in course_tags]
        
        def slide_func(slides):
            if not slides:
                return []
            slides = slides.get_info()
            if not slides:
                return []
            slides_xml = []
            for slide_num, slide_text in slides:
                try:
                    slides_xml.append(
                        E.slide(
                            E.slideno(str(slide_num)),
                            E.text(slide_text),
                        ))
                # Sometimes get 'ValueError: All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters'
                except ValueError:
                    continue
            return slides_xml

        def slice_func(transcript):
            if not transcript:
                return []
            slice_xml = []
            for time, text in transcript:
                slice_xml.append(
                    E.slice(
                        E.time_slice(time),
                        E.text_slice(text)
                    )
                )
            return slice_xml

        def lecture_func(lectures):
            if not lectures:
                return []
            lectures = lectures.get_info()
            lectures_xml = []
            for lecture in lectures:
                lecture_title, lecture_pdf_url, lecture_num, slides, videos = lecture
                videos = videos.get_info()
                for video in videos:
                    video_title, video_url, transcript = video
                    lectures_xml.append(
                        E.lecture(
                            E.lecture_title(lecture_title),
                            E.lecture_pdf_url(lecture_pdf_url),
                            E.lectureno(lecture_num),
                            E.slides(
                                *slide_func(slides)
                            ),
                            E.videos(
                                E.video(
                                    E.video_url(video_url),
                                    E.video_title(video_title),
                                    E.transcript(
                                        *slice_func(transcript)
                                    )
                                )
                            )
                        ))
            return lectures_xml

        # Add course info to XML
        course_title, course_url, course_tags, date, lectures = course.get_info()
        self.course_title = course_title

        xml = (
            E.doc(
                E.source(course_provider.name),
                E.date(date),
                E.course(
                    E.course_url(course_url),
                    E.course_title(course_title),
                    E.course_tags(
                        *tag_func(course_tags)
                    )
                ),
                E.lectures(
                    *lecture_func(lectures)
                )
            )
        )

        self._store_xml(course_provider, xml)
    
    def _store_xml(self, course_provider, xml):
        """ Store the structure in appropriate directory in consistent way 
        Args:
            course_provider: type CourseProviders (enum, e.g CourseProviders.MIT)
        """
        # If course provider directory does not already exist
        if not os.path.exists(course_provider.name):
            os.makedirs(course_provider.name)
        # Store XML in directory
        dirname = os.path.dirname(__file__)
        # cleans name for the case where "/" is in a course title
        provider_clean = self.clean_name(course_provider.name)
        filename_clean = self.clean_name("{}.xml".format(self.course_title[:20]))
        save_path = os.path.join(dirname, provider_clean, filename_clean)
        with open(save_path, 'w') as f:
            f.write(etree.tostring(xml,pretty_print=True).decode())
            
    def clean_name(self, name):
        return name.replace('/','_')
    
        
        