# Web Scraper for Cookies
This Python script uses Selenium to scrape cookies from webpages and export them to an Excel file for further analysis. It sets up a headless web driver (Firefox or Chrome), retrieves cookies from a specified website, and saves the cookie data in an Excel file.

## Features
- Scrapes cookies from a specified URL using Selenium WebDriver.
- Formats the cookies to improve readability and consistency.
- Exports the cookies data to an Excel file.
- Supports headless browsing mode (where no browser window is opened during the scraping process).
- Logs the process, including successful operations and error messages.
- Handles errors related to WebDriver setup and cookie retrieval.
- Automatically cleans up resources (webdriver, temporary directory), even on failures.

## Prerequisites
Before running this script, you need the following:
- Python 3.x+
- Browser and the associated webdriver:
  - Firefox and [geckodriver](https://github.com/mozilla/geckodriver/releases)
  - Chrome and [chromedriver](https://developer.chrome.com/docs/chromedriver/downloads)
- Required libraries: 
  - os
  - shutil
  - tempfile
  - urllib
  - datetime
  - selenium
  - pandas
  - logging
  - PyCryptodome
    - only used with `browser_type = chrome` and `cookie_method = database`
  - sqlite3
    - only used with `cookie_method = database`

You can install the required libraries using `pip` or your preferred package manager. The full list of required packages is in [requirements.txt](requirements.txt).

## Configuration
Configuration options are set within the script itself. 

### Configuration Options
- `browser_type` *Required, String* The type of browser that should be used. **Not** case sensitive.
  - `firefox` uses Firefox and the associated geckodriver.
  - `chrome` uses Chrome and the associated chromedriver. **Note** this specifically refers to Chrome, not any chromium-based browser.
- `cookie_method` *Required, String* The method that should be used to fetch cookies. **Not** case sensitive.
  - `webdriver` uses the built-in Selenium webdriver `.get_cookies()` method. 
  - `database` reads the cookies from the `sqlite` cookies file instead.
- `url` *Required, String* The URL to visit to access cookies. See the [Customization](#Customization) section below for more information.
- `headless` *Optional, Boolean* Whether or not to start the browser in headless mode. If `True`, the browser window will not be visible. If `False`, the browser window will be visible while the script is running.
- `add_sample_cookies_flag` *Optional, Boolean* Whether or not to add the sample cookies to the page. If `True`, sample cookies will be added to the page.
- `export_file` *Optional, String* The file path of the export data (`f'cookies_data_{browser_type}_{cookie_method}.xlsx'` by default).

## Usage
To run the script with the default settings, execute it from the command line. Otherwise, modify the configuration settings within `scrape_cookies.py` and then run the script.

### Example
```bash
python3 scrape_cookies.py
```

## File Output
The script outputs an Excel file (such as `cookies_data_firefox_webdriver.xlsx`) that contains the cookies for the visited page. The columns included in the output file depends on the `browser_type` and `cookie_method` used. Each export file should, at minimum, contain the following columns: 

- `name` The name of the cookie.
- `value` The value of the cookie. *Note:* for chrome database cookies, this column might be named `decrypted_value` instead.
- `path` The URL path that must exist in the requested URL in order for the cookie to have been set.
- `domain` The domain specifying which servers can receive the cookie.
- `secure` Whether the cookie is restricted to HTTPS protocols.
- `httpOnly` Whether the cookie can't be accessed by JavaScript. If `True`, the cookie cannot be accessed by JavaScript.
- `sameSite` The policy specifying whether/when cookies are sent with cross-site requests. Typically will be `Strict`, `Lax`, or `None`.
- `expiry` The date after which to delete the cookie. For webdriver cookies, this will be an epoch time. For database cookies, this will be a datetime. If the cookie does not have an expiry, then the value will be listed as `session`.

There may be additional columns in the export file (such as `priority` or `creationTime`), especially if the `cookie_method` is set to `database`. 

### Example
| name          | value                        | path | domain                | secure | httpOnly | sameSite | expiry     |
|---------------|------------------------------|------|-----------------------|--------|----------|----------|------------|
| sampleCookie1 | this is a secure sample cookie | /    | www.pineconedata.com  | True   | FALSE    | Lax      | 1736828073 |


### Column Mappings
There are a few columns for the `database` `cookie_method` that store raw integer value instead of string values. For example, certain columns like `sameSite` are mapped from integer values like `2` to strings like `Lax`. The formatting step maps the integer values to the string values. The mappings were defined by looking at the source code for each browser. 
- Firefox file: [nsICookie.h](https://searchfox.org/mozilla-central/source/__GENERATED__/dist/include/nsICookie.h)
- Chrome file: [sqlite_persistent_cookie_store.cc](https://source.chromium.org/chromium/chromium/src/+/main:net/extras/sqlite/sqlite_persistent_cookie_store.cc;l=5)

## Process 
At a high level, the script will: 
1. Setup WebDriver
   - The script uses Selenium WebDriver with a browser to scrape cookies.
   - The `setup_driver()` function sets up the WebDriver with the necessary configurations.
2. Get Cookies
   - Once the WebDriver is set up, visits the configured URL and retrieves the cookies associated with the page using the `.get_cookies()` function.
   - Cookies are retrieved using either the webdriver's built-in `get_cookies()` function (if `cookie_method == 'webdriver'` or from the cookies `sqlite` file (if `cookie_method == 'database'`). 
   - The cookies are stored in a pandas DataFrame.
3. Format Cookies
   - The cookies are formatted using either `format_cookies_firefox` or `format_cookies_chrome`, depending on the `browser_type`. 
   - Cookie formatting logic differs slightly between the `browser_type`s and `cookie_method`s. 
4. Export Cookies to Excel
   - The retrieved cookies are then exported to an Excel file using the `export_cookies()` function.
5. Cleanup Resources
   - The webdriver and any associated temporary directories are automatically cleaned up at the end of the process (even in the case of errors).

## Logging
The script logs important events, including errors, to help you debug and track the validation process. Logs are printed to the console in the format:
```bash
YYYY-MM-DD HH:MM:SS - LEVEL: Message
```

### Example
```bash
2025-01-06 18:14:31,977 - INFO: Setting up the selenium WebDriver for firefox...
2025-01-06 18:14:33,667 - INFO: Adding sample cookies...
2025-01-06 18:14:33,680 - INFO: Getting cookies using the webdriver method...
2025-01-06 18:14:33,690 - INFO: Cookies found: 3
2025-01-06 18:14:33,691 - INFO: Exporting cookies...
2025-01-06 18:14:33,709 - INFO: Cookies exported to: cookies_data_firefox_webdriver.xlsx
2025-01-06 18:14:34,315 - INFO: Cleaned up webdriver.
2025-01-06 18:14:34,315 - INFO: Cleaned up profile directory at /tmp/rust_mozprofileqjOL3H (previously removed or does not exist)
```

## Customization
- To scrape cookies from a different webpage, modify/add `driver` commands within the script (`driver.get()`, `driver.execute_script()`, `driver.find_element...().click()`, etc.). 
- The script currently exports cookies from a single URL, but you can extend it to handle multiple URLs by modifying the `__main__` section to loop through a list of URLs.
- The script uses a Firefox or Chrome browser (headless by default). You can modify it to use a different browser (e.g., Chromium, Brave, Edge, Opera) by changing the WebDriver setup.

### Windows OS
The script is currently configured to run on a Linux operating sytem. If you want to use this script on Windows, several modifications will need to be made, including: 
- Multiple paths in the script will need the syntax updated (such as `database_path = f'{profile_dir}/cookies.sqlite'` to `database_path = f'{profile_dir}\\cookies.sqlite'` or to `database_path = os.path.join(profile_dir, 'cookies.sqlite')` or to use `pathlib` from the `Path` library).
- For the `database` access method, the location of the cookies `sqlite` file within the `profile_dir` might be different. For example, the location on Linux is `database_path = f'{profile_dir}/Default/Cookies'`, but on Windows the location might instead be `database_path = f'{profile_dir}/Default/Network/Cookies'`.
- For the `database` access method and the `chrome` browser, decrypting the cookie values might be substantially different. Here is an alternate way to decrypt cookies on Windows that might work:

```python
import base64
import win32crypt
from Cryptodome.Cipher import AES


def get_decryption_key():
    """Get the encryption key, decrypt it, and return the decrypted key value."""
    encrypted_key = None
    with open(path_to_user_profile + '\\Local State', 'r') as file:
        encrypted_key = json.load(file)['os_crypt']['encrypted_key']
    encrypted_key = base64.b64decode(encrypted_key)
    encrypted_key = encrypted_key[5:]
    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return decrypted_key


def decrypt_cookie_values(encrypted_value):
    """Decrypts an encrypted value using the key and returns the decrypted string."""
    decryption_key = get_decryption_key()
    try:
        cipher = AES.new(decryption_key, AES.MODE_GCM, nonce=encrypted_value[3:3+12])
        decrypted_value = cipher.decrypt_and_verify(encrypted_value[3+12:-16], encrypted_value[-16:]).decode('utf-8')
    except:
        decrypted_value = win32crypt.CryptUnprotectData(encrypted_value, None, None, 0)[1].decode('utf-8') or 0
    return decrypted_value
```
    
## Troubleshooting
- WebDriver Not Found
   - Ensure that the geckodriver or chromedriver is correctly installed and added to your system's `PATH`.
- WebDriver Not Setup
   - Ensure that your driver and your browser have the same major version number. 
- Timeout Errors
   - Ensure that the website you're trying to scrape is accessible, and that the connection is stable.
- Export Errors
   - Try installing XlsxWriter and ensuring you have the most up-to-date version of pandas.
- Decryption Errors
   - There are multiple ways the cookies could be encrypted (this only applies to the Chrome database method). If the script throws a `ValueError(f'Unsupported cookie encryption version: {version}')`, you'll need to figure out where the encryption key is stored. Here are a few places that it could be:
     - It could be stored in the `profile_dir + 'Local State'` file. In this case, the key might be `encryption_key = json.load(file)['os_crypt']['encrypted_key']` 
     - It might be stored in the `gnome-keyring` or `KWallet`. 
     - This [article](https://itnext.io/chromium-linux-keyrings-secret-service-passwords-encryption-and-store-d2b30d87ec08) discusses these different methods in the context of credentials storage (username and passwords) instead of cookies specifically, but the concepts and some of the steps are the same.
- Other Errors
   - This script assumes that the website you're scraping allows cookies to be accessed. Some websites may have protections against web scraping or cookie access.
    
## License
This project is licensed under the MIT License. See the LICENSE file in this repository for more details.
