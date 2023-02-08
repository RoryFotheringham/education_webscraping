import time 
import pandas as pd 
from selenium import webdriver 
from selenium.webdriver import Chrome 
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By 
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

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
        
    def get_transcript(self, abs_url):
        self.driver.get(abs_url)
        
        source = self.driver.page_source
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        scripts = soup.find_all('script')
        content = ''
        for script in scripts:
            if '__PAGE_SETTINGS__' in script[:100]:
                content = script
                break
            
        print()
        # tab = self.driver.find_element(By.ID, 'ka-videoPageTabs-tabbedpanel-tab-1')
        # #print(tab)
        # time.sleep(5)

        # self.driver.execute_script('arguments[0].click', tab)
        # #tab.click()
        #self.driver.get(abs_url)
        

