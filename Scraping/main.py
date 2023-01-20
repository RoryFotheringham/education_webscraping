import requests
import PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import xml.etree.cElementTree as ET


""" XML Format 

doc = ET.Element("doc")
ET.SubElement(doc, "lectureno")
ET.SubElement(doc, "course")
ET.SubElement(doc, "date")
ET.SubElement(doc, "headline")

slides = ET.SubElement(doc, "slides")
slide = ET.SubElement(slides, "slide")
ET.SubElement(slide, "slideno")
ET.SubElement(slide, "text")

ET.SubElement(doc, "source")

tree = ET.ElementTree(doc)
tree.write("index_format.xml")

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