import os
import sys
import pandas
import shutil
import sqlite3
import logging
import selenium
import tempfile
from selenium import webdriver
from selenium.webdriver import FirefoxOptions, ChromeOptions
from selenium.webdriver.chrome.service import Service


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


def setup_driver(browser_type, headless=False):
    """Setup the webdriver with necessary options for given browser type."""
    try:
        logging.info(f'Setting up the selenium WebDriver for {browser_type}...')

        if browser_type.lower() == 'firefox':
            options = FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
            profile_dir = driver.capabilities['moz:profile']

        elif browser_type.lower() == 'chrome':
            service = Service('/usr/bin/chromedriver')
            options = ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            tempdir = tempfile.mkdtemp(dir=os.getcwd())
            options.add_argument(f'--user-data-dir={tempdir}')
            driver = webdriver.Chrome(options=options, service=service)
            profile_dir = driver.capabilities['chrome']['userDataDir']

        else:
            raise ValueError(f'Unsupported browser type: {browser_type}')
            sys.exit(1)

        return driver, profile_dir
    except selenium.common.exceptions.SessionNotCreatedException as e:
        logging.error(f'Unable to create WebDriver session. Details: {e}')
        sys.exit(1)
    except selenium.common.exceptions.WebDriverException as e:
        logging.error(f'Issue with the WebDriver. Details: {e}')
        sys.exit(1)
    except Exception as e:
        logging.error(f'Encountered error setting up WebDriver. Details: {e}')
        sys.exit(1)


def get_cookies(driver, browser_type, cookie_method, profile_dir):
    """Call the appropriate get_cookies_ function based on the given cookie_method."""
    logging.info(f'Getting cookies from the {cookie_method}...')
    if cookie_method.lower() == 'webdriver':
        cookies_df = get_cookies_wd(driver)
    elif cookie_method.lower() == 'database':
        cookies_df = get_cookies_db(browser_type, profile_dir)
    else:
        raise ValueError(f'Unsupported cookie method: {cookie_method}')
        sys.exit(1)
    logging.info(f'Cookies found: {len(cookies_df)}')
    return cookies_df


def get_cookies_wd(driver):
    """Get cookies from the given WebDriver and return the data in a DataFrame."""
    try:
        cookies = driver.get_cookies()
        cookies_df = pandas.DataFrame(cookies)
        return cookies_df
    except selenium.common.exceptions.TimeoutException as e:
        logging.error(f'Timeout while trying to retrieve cookies: {e}')
    except selenium.common.exceptions.WebDriverException as e:
        logging.error(f'WebDriver error encountered while getting cookies. Details: {e}')
    except Exception as e:
        logging.error(f'Encountered error getting cookies. Details: {e}')


def get_cookies_db(browser_type, profile_dir):
    """Get cookies from the given browser's cookie database and return the data in a DataFrame."""
    try:
        if browser_type.lower() == 'firefox':
            query = 'SELECT * FROM moz_cookies'
            database_path = f'{profile_dir}/cookies.sqlite'
            temp_db = f'{os.getcwd()}/cookies.sqlite'
        elif browser_type.lower() == 'chrome':
            query = 'SELECT * FROM cookies'
            database_path = f'{profile_dir}/Default/Cookies'
            temp_db = f'{os.getcwd()}/Cookies'

        if not os.path.exists(database_path):
            raise ValueError(f'Cookies database not found at: {database_path}')
            sys.exit(1)

        shutil.copy(database_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cols = [description[0] for description in cursor.description]
        os.remove(temp_db)

        cookies_df = pandas.DataFrame(data=rows, columns=cols)
        return cookies_df
    except Exception as e:
        logging.error(f'Encountered error getting cookies. Details: {e}')


def export_cookies(df, excel_writer, **kwargs):
    """Export the DataFrame to an Excel file."""
    try:
        logging.info('Exporting cookies...')
        df.to_excel(excel_writer, **kwargs)
        logging.info(f'Cookies exported to: {excel_writer}')
    except Exception as e:
        logging.error(f'Encountered error exporting cookies to Excel. Details: {e}')


def add_sample_cookies(driver):
    """Add sample cookies to the given WebDriver instance."""
    driver.add_cookie({
        "name": "sampleCookie1",
        "value": "this is a secure sample cookie",
        "secure": True,
        "httpOnly": False,
        "expiry": 1735673037,
        "sameSite": "Lax"
    })
    driver.add_cookie({
        "name": "sampleCookie2",
        "value": "this is a HTTP Only sample cookie",
        "secure": True,
        "httpOnly": True,
        "expiry": 1735673100,
        "sameSite": "Strict"
    })
    driver.add_cookie({
        "name": "sampleCookie3",
        "value": "this is another sample cookie",
        "secure": False,
        "httpOnly": True,
        "sameSite": "None"
    })
    return driver


if __name__ == "__main__":
    headless = True
    browser_type = 'firefox'
    cookie_method = 'webdriver'
    url = 'https://www.pineconedata.com/'
    export_file = f'cookies_data_{browser_type}_{cookie_method}.xlsx'

    driver, profile_dir = setup_driver(browser_type, headless)
    driver.get(url)
    driver = add_sample_cookies(driver)
    cookies = get_cookies(driver, browser_type, cookie_method, profile_dir)
    export_cookies(cookies, export_file, index=False)

    driver.quit()
