from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import unittest
import requests as req
import start_docker
import pymysql
import socket

# start mysql docker database
start_docker.main()
ip = socket.gethostbyname(socket.gethostname())
conn = pymysql.connect(
    host=ip,
    port=7200,
    user='root',
    password='',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
conn.cursor().execute("create database if not exists testDB;")
conn.cursor().execute("use testDB;")
conn.cursor().execute("create table if not exists search_results(ID INT not null primary key, title text, description text, tags text, time text, language text, stars text);")


class GithubChecker(unittest.TestCase):
    def setUp(self):

        # creates a new chrome session
        self.driver = webdriver.Chrome(ChromeDriverManager().install())

    def test_github(self):
        driver = self.driver

        # Go to github.com
        driver.get("https://www.github.com")
        driver.maximize_window()
        driver.implicitly_wait(4)

        # Search selenium
        search_element = driver.find_element_by_name("q")
        search_element.send_keys("selenium")
        search_element.submit()
        navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
        response_start = driver.execute_script("return window.performance.timing.responseStart")
        dom_complete = driver.execute_script("return window.performance.timing.domComplete")

        backend_performance = response_start - navigation_start
        frontend_performance = dom_complete - response_start

        # Analise results and insert them to the db
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
            for tag in tags:
                tags_text = tag.text.replace('\n', ',')
            conn.cursor().execute("insert ignore into search_results (ID, title, description, tags, time, language, stars) values (%s, %s, %s, %s, %s, %s, %s);", (str(counter), title, description, tags_text, time_text, language, stars))
            counter = counter + 1
        print("Elements data Entered the database successfully\n")

        # Check links validation.
        for item in items:
            title_element = item.find_element_by_tag_name("h3")
            link = title_element.find_element_by_tag_name("a")
            href = link.get_attribute("href")
            resp = req.get(href)
            assert int(resp.status_code) < 400
        print("All links are valid\n")

        # Time performance
        print("Performance time:")
        print("Back End: %s ms" % backend_performance)
        print("Front End: %s ms" % frontend_performance)

    def tearDown(self):
        conn.commit()
        self.driver.quit()
