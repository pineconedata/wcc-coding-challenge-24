import os
import sys
import shutil
import sqlite3
import logging
import selenium
import tempfile
import pandas as pd
from selenium import webdriver
from selenium.webdriver import FirefoxOptions, ChromeOptions
from selenium.webdriver.chrome.service import Service


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


def win_to_unix_epoch(win_epoch):
    """Convert Windows epoch to Unix epoch and return Unix epoch."""
    WIN_EPOCH_TO_UNIX_OFFSET = 11644473600
    MICROSECONDS_IN_SECOND = 1000000

    if not isinstance(win_epoch, (int, float)):
        raise ValueError('win_epoch must be an integer or float.')

    unix_epoch = (win_epoch / MICROSECONDS_IN_SECOND) - WIN_EPOCH_TO_UNIX_OFFSET
    return unix_epoch


def setup_driver(browser_type, headless=False):
    """Setup the webdriver with necessary options for given browser type."""
    try:
        logging.info(f'Setting up the selenium WebDriver for {browser_type}...')

        if browser_type == 'firefox':
            options = FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
            profile_dir = driver.capabilities['moz:profile']

        elif browser_type == 'chrome':
            service = Service('/usr/bin/chromedriver')
            options = ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            tempdir = tempfile.mkdtemp(dir=os.getcwd(), prefix='chromedriver_')
            options.add_argument(f'--user-data-dir={tempdir}')
            driver = webdriver.Chrome(options=options, service=service)
            profile_dir = driver.capabilities['chrome']['userDataDir']

        else:
            raise ValueError(f'Unsupported browser type: {browser_type}')

        return driver, profile_dir
    except selenium.common.exceptions.SessionNotCreatedException as e:
        logging.error(f'Unable to create WebDriver session. Details: {e}')
        raise
    except selenium.common.exceptions.WebDriverException as e:
        logging.error(f'Issue with the WebDriver. Details: {e}')
        raise
    except Exception as e:
        logging.error(f'Encountered error setting up WebDriver. Details: {e}')
        raise


def get_cookies(driver, browser_type, cookie_method, profile_dir):
    """Call the appropriate get_cookies_ function based on the given cookie_method."""
    logging.info(f'Getting cookies using the {cookie_method} method...')
    if cookie_method == 'webdriver':
        cookies_df = get_cookies_wd(driver)
    elif cookie_method == 'database':
        cookies_df = get_cookies_db(browser_type, profile_dir)
    else:
        raise ValueError(f'Unsupported cookie method: {cookie_method}')
    logging.info(f'Cookies found: {len(cookies_df)}')
    return cookies_df


def get_cookies_wd(driver):
    """Get cookies from the given WebDriver and return the data in a DataFrame."""
    try:
        cookies = driver.get_cookies()
        return pd.DataFrame(cookies)
    except selenium.common.exceptions.TimeoutException as e:
        logging.error(f'Timeout while trying to retrieve cookies: {e}')
    except selenium.common.exceptions.WebDriverException as e:
        logging.error(f'WebDriver error encountered while getting cookies. Details: {e}')
    except Exception as e:
        logging.error(f'Encountered error getting cookies from webdriver. Details: {e}')
        raise


def get_cookies_db(browser_type, profile_dir):
    """Get cookies from the given browser's cookie database and return the data in a DataFrame."""
    try:
        if browser_type == 'firefox':
            query = 'SELECT * FROM moz_cookies'
            database_path = f'{profile_dir}/cookies.sqlite'
            temp_db = f'{os.getcwd()}/cookies.sqlite'
        elif browser_type == 'chrome':
            query = 'SELECT * FROM cookies'
            database_path = f'{profile_dir}/Default/Cookies'
            temp_db = f'{os.getcwd()}/Cookies'
        else:
            raise ValueError(f'Unsupported browser: {browser_type}')

        if not os.path.exists(database_path):
            raise ValueError(f'Cookies database not found at: {database_path}')

        shutil.copy(database_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cols = [description[0] for description in cursor.description]
        os.remove(temp_db)

        return pd.DataFrame(data=rows, columns=cols)
    except Exception as e:
        logging.error(f'Encountered error getting cookies from database. Details: {e}')
        raise


def format_cookies(df):
    """Format given cookies dataframe."""
    try:
        logging.info('Formatting cookies...')
        bool_cols = ['is_secure', 'is_httponly', 'has_expires', 'is_persistent', 'has_cross_site_ancestor']
        time_cols = ['creation_utc', 'expires_utc', 'last_access_utc', 'last_update_utc']
        df['priority'] = df['priority'].replace({0: 'Low', 1: 'Medium', 2: 'High'})
        df['samesite'] = df['samesite'].replace({0: 'None', 1: 'Lax', 2: 'Strict'})
        df[bool_cols] = df[bool_cols].astype(bool)
        df[time_cols] = df[time_cols].apply(
            lambda col: pd.to_datetime(
                col.apply(win_to_unix_epoch), unit='s', utc=True, errors='coerce').dt.tz_localize(None)
        )
        return df
    except Exception as e:
        logging.error(f'Encountered error formatting cookies. Details: {e}')
        raise


def export_cookies(df, excel_writer, **kwargs):
    """Export the DataFrame to an Excel file."""
    try:
        logging.info('Exporting cookies...')
        df.to_excel(excel_writer, **kwargs)
        logging.info(f'Cookies exported to: {excel_writer}')
    except Exception as e:
        logging.error(f'Encountered error exporting cookies to Excel. Details: {e}')
        raise


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


def cleanup(driver=None, profile_dir=None):
    """Clean up resources including the webdriver and associated profile directory."""
    if driver:
        try:
            if driver.service.is_connectable():
                driver.quit()
                logging.info('Cleaned up webdriver.')
            else:
                logging.info('Cleaned up webdriver (previously quit or session is no longer active).')
        except selenium.common.exceptions.WebDriverException as e:
            logging.error(f'WebDriverException encountered when quitting the webdriver. Details: {e}')
        except Exception as e:
            logging.error(f'Error while quitting the driver. Details: {e}')

    if profile_dir:
        try:
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir)
                logging.info(f'Cleaned up profile directory at {profile_dir}')
            else:
                logging.info(f'Cleaned up profile directory at {profile_dir} (previously removed or does not exist)')
        except Exception as e:
            logging.error(f'Error while removing profile directory. Details: {e}')


if __name__ == "__main__":
    driver = None
    profile_dir = None

    try:
        headless = True
        browser_type = 'firefox'
        cookie_method = 'webdriver'
        url = 'https://www.pineconedata.com/'
        export_file = f'cookies_data_{browser_type}_{cookie_method}.xlsx'

        browser_type = browser_type.lower()
        cookie_method = cookie_method.lower()
        driver, profile_dir = setup_driver(browser_type, headless)
        driver.get(url)
        driver = add_sample_cookies(driver)

        if not (browser_type == 'chrome' and cookie_method == 'database'):
            cookies = get_cookies(driver, browser_type, cookie_method, profile_dir)

        if cookie_method == 'database':
            if browser_type == 'chrome':
                driver.quit()
                cookies = get_cookies(driver, browser_type, cookie_method, profile_dir)
            cookies = format_cookies(cookies)

        export_cookies(cookies, export_file, index=False)
    except Exception as e:
        logging.error(f'Error: {e}')
    finally:
        cleanup(driver, profile_dir)
