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
        #options.headless = True # it's more scalable to work in headless mode 
        # normally, selenium waits for all resources to download 
        # we don't need it as the page also populated with the running javascript code. 
        options.page_load_strategy = 'none' 
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
        #time.sleep(5)
        elem = None
        ignored_exceptions = (NoSuchElementException,StaleElementReferenceException)
        try:
            elem = WebDriverWait(self.driver, 60, ignored_exceptions=ignored_exceptions).until(EC.presence_of_element_located(("xpath", "//*[contains(text(), '__PAGE_SETTINGS__')]")))
        except TimeoutException:
            print('fetching transcript timed out')
            return []
            
        # we should only be allowed to get to this point
        # if such an element as the one we are looking for exists
        # and has loaded. 
        try:
            scripts = self.driver.find_element("xpath", "//*[contains(text(), '__PAGE_SETTINGS__')]").get_attribute('textContent')
        except NoSuchElementException:
            print("still couldn't find the element")
            return []
        
        
        script = scripts.strip().split('\n')[1]
        
        for count, char in enumerate(script):
            if char == '{':
                script = script[count:]
                break
        
        json_script = json.loads(script[:-1])
        
        new_dict = json_script['hydrate']['wbd']
        
        for key in new_dict.keys():
            if 'ContentForPath' in key:
                right_key = key
                break
        
        subtitles = new_dict[right_key]['data']['contentRoute']['listedPathData']['content']['subtitles']
        
        transcript = []
        
        for sub in subtitles:
            time_raw = sub['startTime']
            time_clean = self.format_time(time_raw)
            text = sub['text']
            slice = Slice(time_clean, text)
            transcript.append(slice)
            
        #self.driver.close()
        
        #time.sleep(5)
        
        return transcript
        
        
        print()
        # tab = self.driver.find_element(By.ID, 'ka-videoPageTabs-tabbedpanel-tab-1')
        # #print(tab)
        # time.sleep(5)

        # self.driver.execute_script('arguments[0].click', tab)
        # #tab.click()
        #self.driver.get(abs_url)
        

