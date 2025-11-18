import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Generator
from logging import getLogger

logger = getLogger(__name__)

load_dotenv()

SELENIUM_URL = os.getenv("SELENIUM_URL")

def _build_options() -> Options:
    """
    Настройки для Chrome.
    """
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--headless")
    return opts

def get_driver() -> Generator[WebDriver, None, None]:
    """
    Dependency для FastAPI: создаёт webdriver.Remote, отдаёт его, а затем закрывает.
    """
    options = _build_options()
    driver = webdriver.Remote(
        command_executor=SELENIUM_URL,
        options=options,
    )
    try:
        yield driver
    finally:
        try:
            driver.quit()
        except Exception as error:
            logger.error(f'Ошибка создания драйвера: {error}')
            pass
