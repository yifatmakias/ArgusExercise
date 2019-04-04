from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import unittest
import httplib2


class GithubChecker(unittest.TestCase):
    def setUp(self):
        # creates a new chrome session
        self.driver = webdriver.Chrome(ChromeDriverManager().install())

    def test_github(self):
        driver = self.driver
        # Go to github.com
        driver.get("https://www.github.com")

        # Search selenium
        search_element = driver.find_element_by_name("q")
        search_element.send_keys("selenium")
        search_element.submit()

        # Analise results
        result_list = self.driver.find_element_by_class_name("repo-list")
        items = result_list.find_elements_by_tag_name("li")
        counter = 1
        for item in items:
            if counter == 6:
                break
            title = item.find_element_by_tag_name("h3").text
            description = item.find_element_by_tag_name("p").text
            tags_xpath = '//*[@id="js-pjax-container"]/div/div[3]/div/ul/li['+str(counter)+']/div[1]/div[1]'
            tags = item.find_elements_by_xpath(tags_xpath)
            time_text = item.find_element_by_tag_name("relative-time").text
            language_xpath = '//*[@id="js-pjax-container"]/div/div[3]/div/ul/li['+str(counter)+']/div[2]/div[1]'
            language = item.find_element_by_xpath(language_xpath).text
            stars = item.find_element_by_class_name("muted-link").text
            print("Title: " + title)
            print("Description: " + description)
            print("Tags: ")
            for tag in tags:
                print(tag.text)
            print("Time: updated " + time_text)
            print("Language: " + language)
            print("Stars: " + stars)
            print("\n")
            counter = counter + 1
        for item in items:
            title_element = item.find_element_by_tag_name("h3")
            link = title_element.find_element_by_tag_name("a")
            href = link.get_attribute("href")
            h = httplib2.Http()
            resp = h.request(href, 'HEAD')
            assert int(resp[0]['status']) < 400

    def tearDown(self):
        self.driver.quit()
