import json
import time 
import pandas as pd 
from selenium import webdriver 
from selenium.webdriver import Chrome 
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By 
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from common import Slice
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

class Transcript_getter:
    def __init__(self):
        # start by defining the options 
        options = webdriver.ChromeOptions() 
        options.headless = True # it's more scalable to work in headless mode 
        # normally, selenium waits for all resources to download 
        # we don't need it as the page also populated with the running javascript code. 
        options.page_load_strategy = 'normal' 
        # this returns the path web driver downloaded 
        chrome_path = ChromeDriverManager().install() 
        chrome_service = Service(chrome_path) 
        # pass the defined options and service objects to initialize the web driver 
        driver = Chrome(options=options, service=chrome_service) 
        driver.implicitly_wait(5)
        
        self.driver = driver
        
    def format_time(self, raw_time):
        secs = int(raw_time)//1000
        convert = str(datetime.timedelta(seconds = secs))
        convert = convert[2:]
        return convert
        
    def quit(self):
        self.driver.quit()
        
    def close(self):
        self.driver.close()
        
    def get_transcript(self, abs_url):
        self.driver.get(abs_url)
        time.sleep(0)
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        settings = ''
        for script in soup.find_all('script'):
            if not script.string:
                continue
            if '__PAGE_SETTINGS__' in script.string[:100]:
                settings = script.string
                break
            
        if settings == '':
            time.sleep(10)
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            for script in soup.find_all('script'):
                if not script.string:
                    continue
                if '__PAGE_SETTINGS__' in script.string[:100]:
                    settings = script.string
                    break
                
        if settings == '':
            print('problem with {}'.format(abs_url))
            print('soup: {}\n'.format(soup.source))
            return []
        
        
        script = settings.strip().split('\n')[1]
        
        for count, char in enumerate(script):
            if char == '{':
                script = script[count:]
                break
        
        json_script = json.loads(script[:-1])

        try:        
            new_dict = json_script['hydrate']['wbd']
        except KeyError:
            return []
            
            
        right_key = ''
        for key in new_dict.keys():
            if 'ContentForPath' in key:
                right_key = key
                break
        if right_key == '':
            return []
        
        try:
            subtitles = new_dict[right_key]['data']['contentRoute']['listedPathData']['content']['subtitles']
        except KeyError:
            return []
        
        transcript = []
        
        for sub in subtitles:
            time_raw = sub['startTime']
            time_clean = self.format_time(time_raw)
            text = sub['text']
            slice = Slice(time_clean, text)
            transcript.append(slice)
            
        print('got transcript for {}'.format(abs_url))
        return transcript
        
        
        print()
        
        

