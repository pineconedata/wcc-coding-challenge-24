import sys
import pandas
import logging
import selenium
from selenium import webdriver
from selenium.webdriver import FirefoxOptions


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


def setup_driver():
    """Setup the webdriver with necessary options."""
    try:
        logging.info('Setting up the selenium WebDriver...')
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


def get_cookies(driver):
    """Get cookies from the given WebDriver and return the data in a DataFrame."""
    try:
        logging.info('Getting cookies...')
        cookies = driver.get_cookies()
        cookies_df = pandas.DataFrame(cookies)
        return cookies_df
    except selenium.common.exceptions.TimeoutException as e:
        logging.error(f"Timeout while trying to retrieve cookies: {e}")
    except selenium.common.exceptions.WebDriverException as e:
        logging.error(f'WebDriver error encountered while getting cookies. Details: {e}')
    except Exception as e:
        logging.error(f'Encountered error getting cookies. Details: {e}')


def export_cookies(writer, df, sheet_name):
    """Export the DataFrame to an Excel file in the specified sheet."""
    try:
        logging.info(f'Exporting cookies for {sheet_name}')
        print(df)
        df.to_excel(writer, sheet_name=sheet_name, index=None)
        writer.close
    except Exception as e:
        logging.error(f'Encountered error exporting cookies to Excel. Details: {e}')


if __name__ == "__main__":
    export_file = 'cookies_data.xlsx'

    driver = setup_driver()

    with pandas.ExcelWriter(export_file, engine='xlsxwriter') as writer:
        homepage_url = 'https://www.pineconedata.com/'
        logging.info(f'Getting cookies for {homepage_url}')
        driver.get(homepage_url)
        driver.add_cookie({"name": "test", "value": "cookie"})
        cookies = get_cookies(driver)
        export_cookies(writer, cookies, 'homepage')

    driver.quit
