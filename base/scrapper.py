from typing import List
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from base.chrome import install_google_chrome, is_chrome_outdated
from time import sleep

import undetected_chromedriver as u_chrome
import random
import os

class Scrapper:
    r"""
            Returns class instance of a simple scrapper (only works with Chrome) V.0.1

            :param *options: Chrome options as str
            :param profile_name: Profile name found at: \path_to_profile\Profile #
            :param path_to_profile: C:\Users\USER\AppData\Local\Google\Chrome\User Data\
    """

    def __init__(self, *options: str, profile_name: str, path_to_profile: str, language="es") -> None:
        self._language = language
        self._options = Options()
        for option in options:
            self._options.add_argument(option)

        agent = UserAgent()
        environment = os.getenv("ENVIRONMENT", "dev")

        self._options.add_argument(f"user-agent={agent.getChrome}")
        self._options.add_argument("--disable-webrtc")
        self._options.add_argument("--no-sandbox")
        if environment != "dev":
            self._options.add_argument("--headless")
        self._options.add_argument("--disable-gpu")
        self._options.add_argument("--disable-dev-shm-usage")
        self._options.add_argument("--window-size=1920x1080")  # Adjust the resolution
        self._options.add_argument("--start-maximized")
        self._options.add_argument("--disable-blink-features=AutomationControlled")

        if is_chrome_outdated():
            install_google_chrome()
        self.browser = u_chrome.Chrome(service=Service(ChromeDriverManager().install()), options=self._options)
        
    def navigate_to(self, website_url) -> None:
        self.browser.get(website_url)

    def quit(self) -> None:
        self.browser.quit()

    def wait(self, timeout: float) -> WebDriverWait:
        """
            Returns a WebDriverWait class instance.

            :param timeout: The value of timeout it has to wait
            :return: Class instance
        """
        return WebDriverWait(self.browser, timeout)

    def isOnWebsite(self, website_title: str) -> bool:
        if (website_title.lower() in self.browser.title.lower()):
            return True
        return False

    def get_elements(self, by: By, value: str) -> List[WebElement]:
        """
            Returns a tuple containing the type of selector and its corresponding value.

            :param by: The type of selector (By.CSS_SELECTOR, By.TAG_NAME, By.ID, etc.)
            :param value: The value of the selector
            :return: A tuple (By.<type>, value)
        """
        ByAllowedValues = [By.CSS_SELECTOR, By.TAG_NAME, By.ID, By.CLASS_NAME, By.NAME, By.LINK_TEXT, By.PARTIAL_LINK_TEXT, By.XPATH]
        if not by in ByAllowedValues: return None

        elements = self.browser.find_elements(by, value)

        return elements

    def is_element_available(element_list: List[WebElement]):
        """
            Returns True if the length of the element_list > 0

            :param element_list: The elements list ( ** List[WebElement] **)
            :return: -> bool
        """
        is_available = False

        if not isinstance(element_list, list):
            raise TypeError("""
                                Parameter type must be List[WebElement]
                            """)
        else:

            for element in element_list:
                if not isinstance(element, WebElement):
                    raise TypeError("""
                                Parameter type must be List[WebElement]
                            """)

            if len(element_list) > 0:
                is_available = True
            else:
                is_available = False

        return is_available


    def execute_sync_script(self, script: str):
        return self.browser.execute_script(script)

    def execute_asynchronous_script(self, script: str):
        return self.browser.execute_async_script(script)

    def await_url(self, url: str) -> bool:
        """
            Method to await the specified url finish loading and let us interact with it.

            :param url: The url to await
        """
        wait = self.wait(timeout=15)
        try:
            is_in_url = wait.until(EC.url_to_be(url))
            return is_in_url
        except:
            return False

    def switch_tab(self) -> str :
        """
            :return original_tab: returns the original_window handle.
        """
        original_tab = self.browser.current_window_handle
        self.browser.switch_to.new_window("window")

        return original_tab
    
    def switch_window(self, window_handle: str):
        self.browser.switch_to.window(window_handle)

    def scroll_to_bottom(self):
        self.browser.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        
    def simulate_human_writing(self, text: str, input: WebElement):
        try:
            for letter in text:
                sleep(random.uniform(0.1, 0.35))
                input.sendKeys(letter)
        except Exception as e:
            print(e)