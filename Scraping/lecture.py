class Lecture:
    def __init__(self, lecno, course, date, headline, url, slides, source):
        self.lecno = lecno
        self.course = course
        self.date = date
        self.headline = headline
        self.url = url
        self.slides = slides
        self.source = source
    

class Slide:
    def __init__(self, slideno, text):
        self.slideno = slideno
        self.text = text