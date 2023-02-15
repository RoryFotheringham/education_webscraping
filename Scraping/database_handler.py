import sqlite3
import os
import xml.etree.ElementTree as ET


class DatabaseHandler:
    """ Handle the database storage of metadata from the XML files """
    METADATA_DIR = os.path.join("database", "metadata.db")
    MIT_DIR = "MIT"
    KHAN_DIR = "KHAN_ACADEMY"

    def __init__(self):
        self.conn_meta = sqlite3.connect(self.METADATA_DIR)
        self.c = self.conn_meta.cursor()
        self.setup_doc_db()
        self.setup_slide_db()
        # Keep track of DOC ID (lecture id) and SLIDE ID (slide id)
        self.doc_id = -1
    
    def setup_doc_db(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS doc_metadata
             (doc_id int unique, source text, course_title text, course_url text, course_tag0 text, course_tag1 text, course_tag2 text, 
             lecture_title text, lecture_num int, lecture_pdf_url text)''')

    def setup_slide_db(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS slide_metadata
             (doc_id int, slide_id int, slide_num int, slide_text text)''')

    def fill_db(self):
        # Go through MIT files first
        print("\n========= MIT ===========\n")
        for f in os.listdir(self.MIT_DIR):
            print("{}\n".format(f))
            self.index_xml(os.path.join(self.MIT_DIR, f))
        print("\n========= KHAN ACADEMY ===========\n")
        for f in os.listdir(self.KHAN_DIR):
            print("{}\n".format(f))
            self.index_xml(os.path.join(self.KHAN_DIR, f))

    def add_doc_metadata(self, doc_id, source, course_title, course_url,
     course_tag0, course_tag1, course_tag2, lecture_title, lecture_num, lecture_pdf_url):
        query = ("INSERT OR REPLACE INTO doc_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
        self.c.execute(query, [doc_id, source, course_title, course_url,
     course_tag0, course_tag1, course_tag2, lecture_title, lecture_num, lecture_pdf_url])
        self.conn_meta.commit()

    def add_page_metadata(self, doc_id, slide_id, slide_num, slide_text):
        query = ("INSERT INTO slide_metadata VALUES (?, ?, ?, ?)")
        self.c.execute(query, [doc_id, slide_id, slide_num, slide_text])
        self.conn_meta.commit()

    def index_xml(self, filein):
        tree = ET.parse(filein)
        root = tree.getroot()

        for elem in root:
            if elem.tag == "source":
                source = elem.text
                continue
            elif elem.tag == "date":
                date = elem.text
                continue
            elif elem.tag == "course":
                course = None
                course_title, course_url, course_tag0, course_tag1, course_tag2 = self.course_info(elem)
                continue
            elif elem.tag == "lectures":
                self.indexLectureElem(elem, source, date, course, course_title, 
                 course_url, course_tag0, course_tag1, course_tag2)

    def course_info(self, root):
        course_title, course_url, course_tag0, course_tag1, course_tag2 = None,None,None,None,None

        for elem in root:
            if elem.tag == 'course_url':
                course_url = elem.text
            if elem.tag == 'course_title':
                course_title = elem.text
            if elem.tag == 'course_tags':
                for i,el in enumerate(elem):
                    if i == 0:
                        course_tag0 = el.text
                    elif i == 1:
                        course_tag1 = el.text
                    elif i == 2:
                        course_tag2 = el.text
        return course_title, course_url, course_tag0, course_tag1, course_tag2

    def indexLectureElem(self, root, source, date, course, course_title,
     course_url, course_tag0, course_tag1, course_tag2):
        lecture_no = -1
        lecture_title, lecture_pdf_url = None,None
        for lecture_elem in root:
            if lecture_elem.tag != "lecture":
                continue
            for elem in lecture_elem:
                if elem.tag == "lecture_title":
                    lecture_title = elem.text
                if elem.tag == "lecture_pdf_url":
                    lecture_pdf_url = elem.text
                if elem.tag == "lectureno":
                    lecture_no += 1
                    self.doc_id += 1
                    # lecture_no = int(elem.text)
                    self.add_doc_metadata(self.doc_id, source, course_title, course_url,
                 course_tag0, course_tag1, course_tag2, lecture_title, lecture_no, lecture_pdf_url)

                if elem.tag != "slides":
                    continue
                # Slides
                if elem.tag == "slides":
                    for subelem in elem:
                        if subelem.tag == "slide":
                            for sl in subelem:
                                if sl.tag == 'slideno':
                                    slide_no = int(sl.text)
                                if sl.tag == 'text':
                                    slide_text = sl.text
                                    self.add_page_metadata(self.doc_id, slide_no, slide_no, slide_text)
                        


if __name__ == '__main__':
    crawler = DatabaseHandler()
    crawler.fill_db()
