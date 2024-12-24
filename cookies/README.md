# Web Scraper for Cookies
This Python script uses Selenium to scrape cookies from webpages and export them to an Excel file for further analysis. It sets up a headless web driver (Firefox or Chrome), retrieves cookies from a specified website, and stores the cookie data in an Excel file with each webpage's cookies saved to a separate sheet.

## Features
- Scrapes cookies from a specified URL using Selenium WebDriver.
- Exports the cookies data to an Excel file with each webpage's cookies stored in a separate sheet.
- Supports headless browsing mode (i.e., no browser window is opened during the scraping process).
- Logs the process, including successful operations and error messages.
- Handles errors related to WebDriver setup and cookie retrieval.

## Prerequisites
Before running this script, you need the following:
- Python 3.x+
- Browser and the associated webdriver:
  - Firefox and [geckodriver](https://github.com/mozilla/geckodriver/releases)
  - Chrome and [chromedriver](https://developer.chrome.com/docs/chromedriver/downloads)
- Required libraries: 
  - selenium
  - pandas
  - logging
  - XlsxWriter

You can install the required libraries using `pip` or your preferred package manager.

## Configuration
Configuration options are set within the script itself. 

### Configuration Options
- `browser_type` *Required, String* The type of browser that should be used. **Not** case sensitive.
  - `firefox` uses Firefox and the associated geckodriver.
  - `chrome` uses Chrome and the associated chromedriver. **Note** this specifically refers to Chrome, not any chromium-based browser.
- `headless` *Optional, Boolean* Whether or not to start the browser in headless mode. If `True`, the browser window will not be visible. If `False`, the browser window will be visible while the script is running. 
- `export_file` *Optional, String* The file path of the export data (`f'cookies_data_{browser_type}.xlsx'` by default).

## Usage
To run the script with the default settings, execute it from the command line.

### Example
```bash
python3 scrape_cookies.py
```

## File Output
The script outputs an Excel file (`cookies_data.xlsx`) that contains the cookies for the visited page(s). Each page's cookies are stored in a separate sheet within the Excel file. The following columns will be included, if they exist: 

- `name` The name of the cookie.
- `value` The value of the cookie.
- `path` The URL path that must exist in the requested URL in order for the cookie to have been set.
- `domain` The domain specifying which servers can receive the cookie.
- `secure` Whether the cookie is restricted to HTTPS protocols.
- `httpOnly` Whether the cookie can't be accessed by JavaScript. If `True`, the cookie cannot be accessed by JavaScript.
- `sameSite` The policy specifying whether/when cookies are sent with cross-site requests.
- `expiry` The date after which to delete the cookie.

### Example
```
name	value	path	domain	secure	httpOnly	sameSite
test	cookie	/	www.pineconedata.com	FALSE	FALSE	None
```

## Process 
At a high level, the script will: 
1. Setup WebDriver: The script uses Selenium with a headless browser to scrape cookies. The `setup_driver()` function sets up the WebDriver with the necessary configurations.
2. Get Cookies: Once the WebDriver is set up, visits any configured webpage(s) and retrieves the cookies associated with the page using the `get_cookies()` function. The cookies are stored in a pandas DataFrame.
3. Export Cookies to Excel: The retrieved cookies are then exported to an Excel file using the `export_cookies()` function. The cookies from each page are stored in their own sheet within the Excel file. 

## Logging
The script logs important events, including errors, to help you debug and track the validation process. Logs are printed to the console in the format:
```bash
YYYY-MM-DD HH:MM:SS - LEVEL: Message
```

### Example
```bash
2024-12-23 18:05:06,633 - INFO: Setting up the selenium WebDriver for firefox...
2024-12-23 18:06:47,584 - INFO: Getting cookies...
2024-12-23 18:06:51,969 - INFO: Cookies found: 10
```

## Customizing the Script
- To scrape cookies from a different webpage, modify/add `driver` commands within the script (`driver.get()`, `driver.execute_script()`, `driver.find_element...().click()`, etc.). 
- The script currently exports cookies from a single URL, but you can extend it to handle multiple URLs by modifying the `__main__` section to loop through a list of URLs.
- The script uses a headless Firefox or Chrome browser by default. You can modify it to use a different browser (e.g., Chromium, Brave, Edge, Opera) by changing the WebDriver setup.

    
## Troubleshooting
- WebDriver Not Found: Ensure that the geckodriver or chromedriver is correctly installed and added to your system's `PATH`.
- WebDriver Not Setup: Ensure that your driver and your browser have the same major version number. 
- Timeout Errors: Ensure that the website you're trying to scrape is accessible, and that the connection is stable.
- Other Errors: This script assumes that the website you're scraping allows cookies to be accessed. Some websites may have protections against web scraping or cookie access.
    
## License
This project is licensed under the MIT License. See the LICENSE file in this repository for more details.
