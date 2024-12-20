# Sitemap Link Validator
This Python script validates URLs from a given sitemap, checking for HTTP errors, exclusions, and specific content conditions. It allows you to parse a sitemap, check URLs for a variety of conditions (like timeout, HTTP errors, specific phrases to exclude, etc.), and record the results into a CSV file.

## Features
- Fetches URLs from a given XML sitemap.
- Validates each URL's HTTP response code and checks for common exceptions like timeouts or HTTP errors.
- Supports exclusion of URLs and content with configurable patterns.
- Extracts additional URLs from the pages and checks them as well.
- Logs details of the validation process and writes the results to a CSV file.
- Easily configurable with a JSON configuration file.

## Prerequisites
- Python 3.x
- Required libraries:
  - requests
  - beautifulsoup4
  - argparse
  - re
  - csv
  - json
  - logging

You can install the required libraries using `pip` or your preferred package manager.

## Configuration
The script uses a configuration JSON file (`config.json`) to define various settings. Here is an example configuration file:
```json
{
  "sitemap_url": "https://www.pineconedata.com/sitemap.xml",
  "urls_to_exclude": ["^https://www.pineconedata.com/404", "https://www.pineconedata.com/ignore"],
  "phrases_to_exclude": ["this page doesn't exist", "link to it is broken", "page error"],
  "first_party_domains": ["www.pineconedata.com"],
  "timeout": 10,
  "data_file": "sitemap_link_validation.csv",
  "extract_additional_urls": true
}
```

### Configuration Options
- `sitemap_url` *Required* The URL of the sitemap to validate.
- `urls_to_exclude` *Optional* A list of URL patterns to exclude from validation.
- `phrases_to_exclude` *Optional* A list of phrases to look for in the page content that should trigger exclusion. Note: these phrases are **not** case-sensitive. 
- `first_party_domains` *Optional* A list of domains considered "first-party" (can be used to identify internal URLs). Should include subdomain, if applicable. 
- `timeout` *Optional* Timeout for HTTP requests (default is 10 seconds).
- `data_file` *Optional* The name (or full filepath) of the CSV file to store results (default is `sitemap_link_validation.csv`).
- `extract_additional_urls` *Optional* Whether to extract and validate additional URLs found on each page in the sitemap. If `false`, the script will only validate links explicitly listed in the sitemap. If `true`, the script will validate sitemap links plus any additional HTTP links found on those pages. 
    
## Usage
To run the script, you can provide a path to a custom configuration file using the `--config` argument or specify the sitemap URL directly via the `--sitemap_url` argument. If neither is specified, the script will check for a `config.json` file in the current working directory. 

### Command Line Arguments
- `--config` *Optional* Path to the configuration file (default is `config.json`).
- `--sitemap_url` *Optional* URL of the sitemap to validate (overrides the value in `config.json`).

### Example
```bash
python validate_sitemap_links.py --config config.json
```

This will fetch URLs from the sitemap specified in `config.json`, validate each URL, and write the results to the specified CSV file.

## CSV Output
The results will be saved in a CSV file (default: `sitemap_link_validation.csv`) with the following columns:

- `URL` The URL that was validated.
- `Response Code` The HTTP response code returned.
- `Exception` The type of exception (if any) encountered during validation (e.g., Timeout, HTTPError).
- `Details` Additional details about the exception (e.g., error message).
- `Response Length` The length of the page response.
- `Page Title` The title of the page (if available).
- `First Party` Whether the URL is from a first-party domain.
- `Link Text` The link text (if available).
- `Source URL` The source URL from which the link was found (e.g., the sitemap or extracted from the page).

### Example Output
```
URL,Response Code,Exception,Details,Response Length,Page Title,First Party,Link Text,Source URL
https://www.pineconedata.com/2024-09-13-basketbal-train-ols/,200,,,140754,Training a Linear Regression Model: Outlier or Caitlin Clark? [Part 5],True,https://www.pineconedata.com/2024-09-13-basketbal-train-ols/,https://www.pineconedata.com/sitemap.xml
https://www.pineconedata.com/2024-07-29-basketball-visualizations/,200,,,104913,Data Visualizations and Feature Selection: Outlier or Caitlin Clark? [Part 4],True,https://www.pineconedata.com/2024-07-29-basketball-visualizations/,https://www.pineconedata.com/sitemap.xml
https://www.pineconedata.com/2024-05-30-basketball-feature_engineering/,200,,,55969,Feature Engineering: Outlier or Caitlin Clark? [Part 3],True,https://www.pineconedata.com/2024-05-30-basketball-feature_engineering/,https://www.pineconedata.com/sitemap.xml
```

## Process
At a high level, here's the process the script follows: 
1. Load Config: The script loads the configuration details from a JSON file.
2. Fetch Sitemap: It sends a GET request to fetch the sitemap (either via URL or from the config file).
3. Validate URLs: For each URL in the sitemap:
   - It checks whether the URL matches any exclusion patterns.
   - Sends a GET request to the URL, checks the response code, and looks for any content exclusions (such as specific phrases).
   - Extracts additional URLs from the page content if specified.
4. Write Results: The results (including exceptions, response codes, page titles, etc.) are written to a CSV file.
5. Extract Additional URLs: If enabled, the script will also extract and validate additional URLs found on the pages.

## Logging

The script logs important events, including errors, to help you debug and track the validation process. Logs are printed to the console in the format:
```bash
YYYY-MM-DD HH:MM:SS - LEVEL: Message
```

### Example
```bash
2024-12-18 15:55:50,395 - INFO: Parsing sitemap content.
2024-12-18 15:55:50,396 - INFO: Parsed sitemap content. Found 15 URLs.
2024-12-18 15:55:50,396 - INFO: Validating url at https://www.pineconedata.com/2024-09-13-basketbal-train-ols/
```

## License 
This project is licensed under the MIT License. See the LICENSE file in this repository for more details.