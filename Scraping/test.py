from lxml import etree
from lxml.builder import E
import os

def tag_func(course_tags):
    if not course_tags:
        return []
    return [E("list", a) for a in course_tags]

def slides_func(slides):
    slides_xml = []
    for i, slide in enumerate(slides):
        slides_xml.append(
            E.slide(
                E.slideno(str(i)),
                E.text(slide)
            )
        )
    return slides_xml

xml = (
    E.doc(
        E.source("MIT"),
        E.date("28/01/2023"),
        E.course(
            E.course_url("https://dummylink.com"),
            E.course_title("Dummy title"),
            E.course_tags(
                *tag_func(None)
            )
        ),
        E.lectures(
            E.lecture(
                E.lecture_title(),
                E.lecture_pdf_url(),
                E.lectureno(),
                E.slides(
                    *slides_func(['slide1', 'slide2', 'slide3'])
                ),
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
)

dirname = os.path.dirname(__file__)
save_path = os.path.join(dirname, "MIT", "{}.xml".format("Mathematical Methods for Engineers II by Prof. Gilbert Strang"))
with open(save_path, 'w') as f:
    f.write(etree.tostring(xml,pretty_print=True).decode())
#print(etree.tostring(xml, pretty_print=True).decode())