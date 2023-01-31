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
        self.videos = None

    def add_lectures_info(self, lectures):
        self.lectures = lectures  # single instance of Lectures obj

    def add_videos_info(self, videos):
        self.videos = videos  # single instance of Videos obj

    def get_info(self):
        return self.course_title, self.course_url, self.course_tags, self.date, self.lectures, self.videos


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

    def insert_slide(self, video_title, video_url, transcript):
        self.struct.add((video_title, video_url, transcript))
    
    def get_info(self):
        return self.struct


class XMLHandler:
    """ Class to handle XML file creation and storage in desired structure for one whole course.
        Simply provide it with course_provider ENUM type and the Course class.
    """
    def __init__(self):
        self.course_title = None

    def build_and_store_xml(self, course_provider, course):
        # Add course info to XML
        course_title, course_url, course_tags, date, lectures, videos = course.get_info()
        self.course_title = course_title

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
            for slide in slides:
                slide_num, slide_text = slide
                try:
                    slides_xml.append(
                        E.slide(
                            E.slideno(str(slide_num)),
                            E.text(slide_text),
                        ))
                # Sometimes get 'ValueError: All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters'
                except ValueError:
                    slides_xml.append(
                        E.slide(
                            E.slideno(str(slide_num)),
                            E.text(""),
                        ))
            return slides_xml

        def lecture_func(lectures):
            if not lectures:
                return []
            lectures = lectures.get_info()
            lectures_xml = []
            for lecture in lectures:
                lecture_title, lecture_pdf_url, lecture_num, slides, videos = lecture
                lectures_xml.append(
                    E.lecture(
                        E.lecture_title(lecture_title),
                        E.lecture_pdf_url(lecture_pdf_url),
                        E.lectureno(lecture_num),
                        E.slides(
                            *slide_func(slides)
                        )
                    ))
            return lectures_xml

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
                    *lecture_func(lectures),
                    E.videos(
                        E.video(
                            E.video_url(),
                            E.video_title(),
                            E.transcript(
                                E.slice(
                                    E.text_slice(),
                                    E.time_slice(),
                                )
                            )
                        )
                    )
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
        save_path = os.path.join(dirname, course_provider.name, "{}.xml".format(self.course_title[:20]))
        with open(save_path, 'w') as f:
            f.write(etree.tostring(xml,pretty_print=True).decode())