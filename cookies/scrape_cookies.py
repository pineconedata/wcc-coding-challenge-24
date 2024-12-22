import sys
import logging
import selenium
from selenium import webdriver
from selenium.webdriver import FirefoxOptions


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


def setup_driver():
    """Setup the webdriver with necessary options."""
    try:
        options = FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        return driver
    except selenium.common.exceptions.SessionNotCreatedException as e:
        logging.error(f'Unable to create WebDriver session. Details: {e}')
        sys.exit(1)
    except selenium.common.exceptions.WebDriverException as e:
        logging.error(f'Issue with the WebDriver. Details: {e}')
        sys.exit(1)
    except Exception as e:
        logging.error(f'Encountered error setting up WebDriver. Details: {e}')


if __name__ == "__main__":
    driver = setup_driver()
    driver.get('https://www.pineconedata.com/')
    title = driver.title
    logging.info(title)
    driver.quit
