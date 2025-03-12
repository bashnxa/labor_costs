import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from config import REDMINE_LOGIN_URL, REDMINE_USERNAME, REDMINE_PASSWORD, REPORT_URL


def get_webdriver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )


def fetch_page_source() -> str:
    with get_webdriver() as driver:
        try:
            driver.get(REDMINE_LOGIN_URL)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(REDMINE_USERNAME)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            ).send_keys(REDMINE_PASSWORD)
            driver.find_element(By.NAME, "login").click()
            time.sleep(3)
            driver.get(REPORT_URL)
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return driver.page_source
        except (TimeoutException, NoSuchElementException) as error:
            return f"Ошибка при загрузке страницы: {error}"
