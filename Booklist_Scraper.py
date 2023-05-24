from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import pandas as pd
import time
import csv
import sys
import numpy as np
import re
import calendar

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 1, "profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.cookies": 1}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver


def scrape_Booklist(path):

    start = time.time()
    print('-'*75)
    print('Scraping Booklist.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()
    months = list(calendar.month_name[1:])
    # initializing the dataframe
    data = pd.DataFrame()
    # if no books links provided then get the links
    if path == '':
        name = 'Booklist_data.xlsx'
        # getting the books under each category
        links = []
        nbooks = 0
        homepage = 'https://www.booklistonline.com/book-awards'
        driver.get(homepage)         
        # scraping category urls
        table = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table[id='Table15']")))
        categories = wait(table, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "p")))[2:]
        cat_links = []
        for category in categories:
            try:
                tags =  wait(category, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
            except:
                continue
            for tag in tags:
                link = tag.get_attribute('href')
                cat_links.append(link)

        # scraping books urls
        for link in cat_links:
            driver.get(link)
            span = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[class='style22']")))
            titles = wait(span, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
            for title in titles:
                try:
                    link = title.get_attribute('href')
                    if 'booklistonline.com' in link:
                        links.append(link)
                        nbooks += 1
                        print(f'Scraping the url for book {nbooks}')
                except Exception as err:
                    print('The below error occurred during the scraping from Booklist.com, retrying ..')
                    print('-'*50)
                    print(err)
                    continue

        # saving the links to a csv file
        print('-'*75)
        print('Exporting links to a csv file ....')
        with open('Booklist_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link'])
            for row in links:
                writer.writerow([row])

    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        name = path.split('\\')[-1][:-4]
        name = name + '_data.xlsx'
    else:
        df_links = pd.read_csv('Booklist_links.csv')

    links = df_links['Link'].values.tolist()

    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    print('-'*75)
    n = len(links)
    for i, link in enumerate(links):

        try:
            if link in scraped: continue
            driver.get(link)           
            details = {}
            print(f'Scraping the info for book {i+1}\{n}')

            # title and title link
            title_link, title = '', ''              
            try:
                title_link = link
                title = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "font[size='5']"))).get_attribute('textContent').replace('\n', '').strip().title() 
            except:
                print(f'Warning: failed to scrape the title for book: {link}')                             
            details['Title'] = title
            details['Title Link'] = title_link    
            
            # Author
            author = ''
            try:
                author = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "font[size='3']"))).get_attribute('textContent').replace('By', '').strip().title()
                if author[-1] == '.':
                    author = author[:-1]
            except:
                pass
                    
            details['Author'] = author                      

            # category and genre
            cat, genre = '', ''              
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='style110 bread-crumbs-up']")))
                tags = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                cat = tags[0].get_attribute('textContent')
                genre = tags[1].get_attribute('textContent')
            except:
                print(f'Warning: failed to scrape the cat and genre for book: {link}')      
                
            details['Category'] = cat
            details['Genre'] = genre  

            # publication date
            date = ''            
            try:
                try:
                    span = wait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(name(), 'parastyle')]")))[-1]
                except:
                    spans = wait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//span[@class='style22']")))
                    if len(spans) == 3:
                        span = spans[1]
                    elif len(spans) == 2:
                        span = spans[0]
                tags = wait(span, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                found = False
                for tag in tags:
                    text = tag.get_attribute('textContent')
                    for month in months:
                        if month in text:
                            date = text.replace('(', '').split('Booklist')[0].strip()
                            found = True
                            break
                    if found: break
            except:
                pass                             
            details['Publication Date'] = date              
           
            # ISBN
            ISBN = ''            
            try:
                try:
                    span = wait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(name(), 'parastyle')]")))[-1]
                except:
                    spans = wait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//span[@class='style22']")))
                    if len(spans) == 3:
                        span = spans[1]
                    elif len(spans) == 2:
                        span = spans[0]
                tags = wait(span, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                found = False
                for tag in tags:
                    text = tag.get_attribute('textContent')
                    if '(' in text and ')' in text:
                        ISBN = text.replace('(', '').replace(')', '').strip()
                        found = True
                        break
                    if found: break
            except:
                pass                             
            details['ISBN'] = ISBN             
            
            # price and grade
            price, grade = '', ''            
            try:
                try:
                    text = wait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(name(), 'parastyle')]")))[-1].get_attribute('textContent')
                except:
                    spans = wait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//span[@class='style22']")))
                    if len(spans) == 3:
                        span = spans[1]
                    elif len(spans) == 2:
                        span = spans[0]
                    text = span.get_attribute('textContent')
                if '$' in text:
                    price = text.split('$')[1].split()[0]
                    price = float(price)
                if 'Grades' in text:
                    grade = text.split('Grades ')[1].split()[0].split('.')[0]
            except:
                pass  
            
            details['Grade'] = grade            
            details['Price'] = price   
             
            
            # appending the output to the datafame        
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                data.to_excel(name, index=False)
        except:
            pass

    # optional output to excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'Booklist.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":

    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_Booklist(path)

