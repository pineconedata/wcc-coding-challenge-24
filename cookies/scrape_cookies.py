import os
import shutil
import sqlite3
import logging
import selenium
import tempfile
import pandas as pd
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from datetime import datetime, timedelta
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
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


def decrypt_value(encrypted_value):
    """Decrypts an encrypted value based on its version and returns the decrypted string."""
    try:
        version, encrypted_value = encrypted_value[:3].decode().lower(), encrypted_value[3:]
        if version.lower() == 'v10':
            key = PBKDF2(password='peanuts'.encode('utf-8'), salt=b'saltysalt', dkLen=16, count=1)
            cipher = AES.new(key, AES.MODE_CBC, IV=b' ' * 16)
            decrypted = cipher.decrypt(encrypted_value)
            padding_length = decrypted[-1]
            return decrypted[32:-padding_length].decode('utf-8')
        else:
            raise ValueError(f'Unsupported cookie encryption version: {version}')
    except Exception as e:
        logging.error(f'Encountered error decrypting cookie values. Details: {e}')
        raise


def format_cookies_chrome(df):
    """Format given cookies dataframe for chrome browser_type."""
    try:
        logging.info('Formatting cookies...')
        samesite_map = {
            -1: '',
            0: 'None',
            1: 'Lax',
            2: 'Strict'
        }
        priority_map = {
            0: 'Low',
            1: 'Medium',
            2: 'High'
        }
        source_scheme_map = {
            0: 'Unset',
            2: 'Secure'
        }
        source_type_map = {
            0: 'Unknown',
            1: 'HTTP',
            2: 'Script',
            3: 'Other'
        }
        df['sameSite'] = df['samesite'].replace(samesite_map)
        df['priority'] = df['priority'].replace(priority_map)
        df['source_scheme'] = df['source_scheme'].replace(source_scheme_map)
        df['source_type'] = df['source_type'].replace(source_type_map)
        bool_cols = ['is_secure', 'is_httponly', 'has_expires', 'is_persistent', 'has_cross_site_ancestor']
        df[bool_cols] = df[bool_cols].astype(bool)

        time_cols = ['creation_utc', 'expires_utc', 'last_access_utc', 'last_update_utc']
        df[time_cols] = df[time_cols].apply(lambda col: pd.to_datetime(
                col.apply(win_to_unix_epoch), unit='s', utc=True, errors='coerce').dt.tz_localize(None)
            )

        df['decryptedValue'] = df['encrypted_value'].apply(decrypt_value).fillna(df['value'])
        cols_to_rename = {
            'is_secure': 'isSecure',
            'is_httponly': 'isHttpOnly',
            'has_expires': 'hasExpires',
            'is_persistent': 'isPersistent',
            'has_cross_site_ancestor': 'hasCrossSiteAncestor',
            'creation_utc': 'creationTime',
            'expires_utc': 'expiry',
            'last_access_utc': 'lastAccessedTime',
            'last_update_utc': 'lastUpdatedTime',
            'source_scheme': 'sourceScheme',
            'source_port': 'sourcePort',
            'source_type': 'sourceType',
            'host_key': 'host'
        }
        df.rename(columns=cols_to_rename, inplace=True)
        cols_to_drop = ['top_frame_site_key', 'samesite', 'value', 'encrypted_value']
        df.drop(columns=cols_to_drop, inplace=True)
        return df
    except Exception as e:
        logging.error(f'Encountered error formatting cookies. Details: {e}')
        raise


def format_cookies_firefox(df):
    """Format given cookies dataframe for firefox browser_type."""
    try:
        logging.info('Formatting cookies...')
        samesite_map = {
            -1: '',
            0: 'None',
            1: 'Lax',
            2: 'Strict'
        }
        source_scheme_map = {
            0: 'Unset',
            1: 'HTTP',
            2: 'HTTPS',
            4: 'File'
        }
        df['sameSite'] = df['sameSite'].replace(samesite_map)
        df['schemeMap'] = df['schemeMap'].replace(source_scheme_map)
        bool_cols = ['isSecure', 'isHttpOnly', 'inBrowserElement', 'isPartitionedAttributeSet']
        df[bool_cols] = df[bool_cols].astype(bool)

        df['lastAccessed'] = pd.to_datetime(df['lastAccessed'], unit='us', errors='coerce').dt.tz_localize(None)
        df['creationTime'] = pd.to_datetime(df['creationTime'], unit='us', errors='coerce').dt.tz_localize(None)
        df['expiry'] = pd.to_datetime(df['expiry'], unit='s', errors='coerce').dt.tz_localize(None)
        df['originAttributes'] = df['originAttributes'].apply(unquote)

        cols_to_rename = {
            'lastAccessed': 'lastAccessedTime'
        }
        df.rename(columns=cols_to_rename, inplace=True)
        cols_to_drop = ['id', 'rawSameSite']
        df.drop(columns=cols_to_drop, inplace=True)
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
    logging.info('Adding sample cookies...')
    current_time_utc = datetime.utcnow()
    one_week_utc = int((current_time_utc + timedelta(weeks=1)).timestamp())
    thirty_day_utc = int((current_time_utc + timedelta(days=30)).timestamp())
    driver.add_cookie({
        "name": "sampleCookie1",
        "value": "this is a secure sample cookie",
        "secure": True,
        "httpOnly": False,
        "expiry": one_week_utc,
        "sameSite": "Lax"
    })
    driver.add_cookie({
        "name": "sampleCookie2",
        "value": "this is a HTTP Only sample cookie",
        "secure": True,
        "httpOnly": True,
        "expiry": thirty_day_utc,
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
    # initialize variables
    driver = None
    profile_dir = None

    try:
        # configuration settings for web scraping
        headless = True
        add_sample_cookies_flag = True
        browser_type = 'firefox'
        cookie_method = 'webdriver'
        url = 'https://www.pineconedata.com/'
        export_file = f'cookies_data_{browser_type}_{cookie_method}.xlsx'

        # normalize variables
        browser_type = browser_type.lower()
        cookie_method = cookie_method.lower()

        # setup webdriver and navigate to page
        driver, profile_dir = setup_driver(browser_type, headless)
        driver.get(url)
        if add_sample_cookies_flag:
            driver = add_sample_cookies(driver)
        WebDriverWait(driver, 45).until(lambda wd: wd.execute_script('return document.readyState') == 'complete')

        # get and format cookies depending on browser type and cookie method
        if not (browser_type == 'chrome' and cookie_method == 'database'):
            cookies = get_cookies(driver, browser_type, cookie_method, profile_dir)
        if cookie_method == 'database':
            if browser_type == 'chrome':
                driver.quit()
                cookies = get_cookies(driver, browser_type, cookie_method, profile_dir)
                cookies = format_cookies_chrome(cookies)
            else:
                cookies = format_cookies_firefox(cookies)
        cookies['expiry'] = cookies['expiry'].fillna('session')

        export_cookies(cookies, export_file, index=False)
    except Exception as e:
        logging.error(f'Error: {e}')
    finally:
        cleanup(driver, profile_dir)
