from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep

import config as C

chrome_options = Options()
chrome_options.add_argument("user-data-dir=" + C.CHROME_COOKIES_DIR)
driver = webdriver.Chrome(options=chrome_options)

class KeynotePresentation:
    def __init__(self, link):
        assert "https://" in link, "www.icloud.com/keynote/" in link

        driver.get(link)
        sleep(240)

    def start_presentation(self):
        start_presentation_button = driver.find_element(By.CLASS_NAME, "play-icon")
        start_presentation_button.click()

    def next_slide(self):
        pass
    def previous_slide(self):
        pass




# for testing only:
if __name__ == "__main__":
    controller = KeynotePresentation(link="https://www.icloud.com/keynote/039FyEI2v0Ns6bFsuktEowUcw#Pr%C3%A4sentation_12")
    controller.start_presentation()
