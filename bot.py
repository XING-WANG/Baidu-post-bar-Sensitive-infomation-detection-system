from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import os
import getpass

class TiebaBot():
    def __init__(self, url):
        super().__init__()
        
        self.bar_main_page = url

        chrome_options = ChromeOptions()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("log-level=3")
        chrome_options.add_argument('Accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
        chrome_options.add_argument('--disable-gpu')
        
        self.driver = Chrome(executable_path='./chromedriver.exe', chrome_options=chrome_options)
        self.driver.set_window_size(1200, 800)

    def tieba_spider(self, max_page_num):
        self.driver.get(url=self.bar_main_page)
        for i in range(max_page_num):
            print(f'No.{i} page')
            self.__verify_by_pass()

            for blog in self.driver.find_elements_by_xpath('//a[@class="j_th_tit "]'):
                ActionChains(self.driver).move_to_element(blog).click(blog).perform()
                windows = self.driver.window_handles
                self.driver.switch_to.window(windows[-1])
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'title'))
                )

                # save blog
                self.__get_blog()

                self.driver.close()
                self.driver.switch_to.window(windows[0])
            
            try:
                next_page = self.driver.find_element_by_xpath('//a[@class="next pagination-item "]')
                next_page_count = int(
                    self.driver.find_element_by_xpath('//span[@class="pagination-current pagination-item "]').get_attribute('textContent').strip()
                ) + 1
                
                ActionChains(self.driver).move_to_element(next_page).click(next_page).perform()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f'//span[@class="pagination-current pagination-item "][text()=\'{next_page_count}\']'))
                )
            except NoSuchElementException as esee:
                print('no next page, exit')
                break
            except TimeoutException as te:
                print('Unknown error, exit')
                break
        # leave a window, no close
        return

    def jubao(self, blog_id, level, reason, content):
        self.driver.get(url=f'https://tieba.baidu.com/p/{blog_id}')
        self.__verify_by_pass()
        self.__login()
        self.driver.get(url=f'https://tieba.baidu.com/p/{blog_id}')
        self.__verify_by_pass()
        
        # find the reply
        while True:
            self.__closePop()
            
            try:
                jubao = self.driver.find_element_by_xpath(f'//div[@class="post-tail-wrap"][span[@class="tail-info"]=\'{level}???\']/span[@class="j_jb_ele"]')
                ActionChains(self.driver).move_to_element(jubao).click(jubao).perform()
                break
            except NoSuchElementException as esee: 
                try:
                    next_page = self.driver.find_element_by_xpath('//li[@class="l_pager pager_theme_4 pb_list_pager"]/a[text()=\'?????????\']')
                    next_page_count = int(
                        self.driver.find_element_by_xpath('//span[@class="tP"]').get_attribute('textContent').strip()
                    ) + 1

                    ActionChains(self.driver).move_to_element(next_page).click(next_page).perform()
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f'//span[@class="tP"][text()=\'{next_page_count}\']'))
                    )
                except NoSuchElementException as esee:
                    print('??????????????????, ????????????id????????????, ??????')
                    return
                except TimeoutException as te:
                    print('Unknown error, end')
                    return

        # switch to new window and wait for loading
        try:
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[-1])
            WebDriverWait(self.driver, 10).until(
                EC.title_contains('????????????')
            )
        except TimeoutException as te:
            print('???????????????????????????, ??????')
            return
        except NoSuchWindowException as nswe:
            print('???????????????????????????, ??????')
            return

        # choose a reason
        try:
            choice = self.driver.find_element_by_xpath(f'//li[label[@data-value="{reason}"]]/i')
        except NoSuchElementException as esee:
            choice = self.driver.find_element_by_xpath(f'//li[label[@data-value="10011"]]/i')
        ActionChains(self.driver).move_to_element(choice).click(choice).perform()

        # 
        text = self.driver.find_element_by_xpath('//textarea[@id="reason"]')
        ActionChains(self.driver).move_to_element(text).click(text).perform()
        text.send_keys(content)

        # submit
        submit = self.driver.find_element_by_xpath('//input[@class="form-submit btn"]')
        ActionChains(self.driver).move_to_element(submit).click(submit).perform()

        # verify_by_pass
        print('by pass begin')
        while True:
            angle = random.choice([45, 90, 135, 180, 225, 270, 315])
            print(f'test {angle}')
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="vcode-spin-button"]/p'))
            )
            ActionChains(self.driver).drag_and_drop_by_offset(
                self.driver.find_element_by_xpath('//div[@class="vcode-spin-button"]/p'),
                (angle / 360) * 212, 
                0
            ).perform()
            try:
                WebDriverWait(self.driver, 3).until_not(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="vcode-body vcode-body-spin"]'))
                )
                print('success')
                break
            except TimeoutException as te:
                print('failed')
        
        # switch back
        self.driver.close()
        self.driver.switch_to.window(windows[0])

    def __login(self):
        self.__closePop()
        try:
            login = self.driver.find_element_by_xpath('//input[@value="??????"]')
            print('????????????')
        except NoSuchElementException as esee:
            print('?????????????????????, ????????????')
            return

        user_name = self.driver.find_element_by_xpath('//input[@name="userName"]')
        ActionChains(self.driver).move_to_element(user_name).click(user_name).perform()
        user_name.send_keys(input('username: '))

        passwd = self.driver.find_element_by_xpath('//input[@name="password"]')
        ActionChains(self.driver).move_to_element(passwd).click(passwd).perform()
        passwd.send_keys(getpass.getpass('password: '))

        ActionChains(self.driver).move_to_element(login).click(login).perform()

        try:
            WebDriverWait(self.driver, 10).until_not(
                EC.presence_of_element_located((By.XPATH, '//input[@value="??????"]'))
            )
            print('????????????')
        except TimeoutException as te:
            print('????????????')

    def __get_blog(self):
        self.__verify_by_pass()
        
        blog_id = self.driver.current_url.split("/")[-1].split("?")[0]
        blog_title = self.driver.title
        file_name = f'logs/blog-{blog_id}.log'
        if os.path.exists(file_name) and os.path.isfile(file_name):
            print(f'{file_name} already exists, end')
            return
        print(f'{file_name} saving...')
        f = open(file_name, 'w', encoding='utf-8')
        f.write(f'{blog_id} {blog_title}\n')

        while True:
            self.__verify_by_pass()
            
            # if there is a pop, close it
            self.__closePop()
            
            # save this page
            for reply in self.driver.find_elements_by_xpath('//div[@class="l_post l_post_bright j_l_post clearfix  "]'):      
                reply_user = reply.find_element_by_xpath('.//a[@alog-group="p_author"]').get_attribute('textContent').strip()
                reply_content = reply.find_element_by_xpath('.//div[@class="d_post_content j_d_post_content "]').get_attribute('textContent').replace(' ', '')
                reply_img_srcs = ' '.join(
                    [img.get_attribute('src') for img in reply.find_elements_by_xpath('.//div[@class="d_post_content j_d_post_content "]//img')]
                )  
                reply_info = ' '.join(
                    [info.get_attribute('textContent').strip() for info in reply.find_elements_by_xpath('.//div[@class="post-tail-wrap"]//span[@class="tail-info"]')]
                )
                
                f.write(f'{reply_info} {reply_user} {reply_content} {reply_img_srcs}\n')
            
            # try to switch to next page, or exit
            try:
                next_page = self.driver.find_element_by_xpath('//li[@class="l_pager pager_theme_4 pb_list_pager"]/a[text()=\'?????????\']')
                next_page_count = int(
                    self.driver.find_element_by_xpath('//span[@class="tP"]').get_attribute('textContent').strip()
                ) + 1

                ActionChains(self.driver).move_to_element(next_page).click(next_page).perform()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f'//span[@class="tP"][text()=\'{next_page_count}\']'))
                )
            except NoSuchElementException as esee:
                print('no next page, end')
                break
            except TimeoutException as te:
                print('Unknown error, end')
                break
            
        f.close()

    def __verify_by_pass(self):    
        while True:
            if self.driver.title != '??????????????????':
                return
            print('by pass begin')
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//img[@class="vcode-spin-img"]'))
            )
            angle = random.choice([45, 90, 135, 180, 225, 270, 315])
            print(f'test {angle}')
            ActionChains(self.driver).drag_and_drop_by_offset(
                self.driver.find_element_by_xpath("//div[@class=\"vcode-spin-button\"]/p"),
                (angle / 360) * 212, 
                0
            ).perform()
            
            # test success
            try:
                WebDriverWait(self.driver, 3).until_not(
                    EC.title_is('??????????????????')
                )
                print('success')
            except TimeoutException as te: # failed
                print('failed')
                continue
    
    def __closePop(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//span[@class="close-btn"]'))
            )
            close_pop_button = self.driver.find_element_by_xpath('//span[@class="close-btn"]')
            ActionChains(self.driver).move_to_element(close_pop_button).click(close_pop_button).perform()
            print('close a pop')
        except TimeoutException as te:
            print('there is no pop')