import re
import csv
import sys
import json
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def write_data(data_file, url, response_code, exception, details, response_length,
               page_title, url_type):
    with open(data_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url, response_code, exception, details, response_length,
                         page_title, url_type])


def load_config(config_file): 
    with open(config_file, 'r') as f:
        return json.load(f)


def get_url(url, timeout=10):
    try:
        print(f'Retrieving page from {url}')
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        print(f'Retrieved page from {url}')
        return response, None, None
    except requests.exceptions.Timeout as e:
        error_details = f'The request to {url} exceeded the threshold of {timeout}'
        print(f'Error: {error_details}')
        return e.response, 'Timeout', error_details
    except requests.exceptions.HTTPError as e:
        error_details = f'HTTPError {e.response.status_code} - {e.response.reason}'
        print(f'Error: {error_details} at {url}')
        return e.response, 'HTTPError', error_details
    except requests.exceptions.RequestException as e:
        print(f'Error: Failed to fetch page from {url}. Details: {e}')
        return e.response, 'RequestException', str(e)


def parse_sitemap(sitemap_content):
    try:
        print('Parsing sitemap content.')
        soup = BeautifulSoup(sitemap_content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        print(f'Parsed sitemap content. Found {len(urls)} URLs.')
        if not urls:
            print('No URLs found in the sitemap content.')
        return urls
    except Exception as e:
        print(f'Error: Failed to parse the sitemap XML. Details: {e}')
        return []


def extract_domain(url):
    """Extract the domain from the given URL."""
    parsed_url = urlparse(url)
    return parsed_url.netloc


def is_url_first_party(url, first_party_domains):
    """Determine if the URL is first-party (True) or third-party (False)
    based on first_party_domains list."""
    domain = extract_domain(url)
    return domain in first_party_domains


def is_url_excluded(url, urls_to_exclude):
    if url in urls_to_exclude:
        print(f'Skipping {url} as it is in the excluded list.')
        return True
    return False


def contains_excluded_phrases(content, phrases_to_exclude):
    matched_phrases = [phrase for phrase in phrases_to_exclude
                       if re.search(phrase, content.get_text(), re.IGNORECASE)]

    if matched_phrases:
        print(f'Excluded phrase(s) "{matched_phrases}" found in page.')
        return matched_phrases
    return False


def extract_page_title(content):
    try:
        title_tag = content.find('title')
        return title_tag.text if title_tag else None
    except Exception as e:
        print(f'Error: Failed to extract page title. Details: {e}')
        return None


def validate_url(url, urls_to_exclude, phrases_to_exclude, first_party_domains, data_file, timeout):
    # set initial values
    data = {
        'url': url,
        'response_code': None,
        'exception': None,
        'details': None,
        'response_length': 0,
        'page_title': None,
        'url_first_party': None
    }

    # determine if the URL is first-party or third-party
    data['url_first_party'] = is_url_first_party(url, first_party_domains)

    # if url is excluded, log and return early
    if is_url_excluded(url, urls_to_exclude):
        data['exception'] = 'Excluded URL'
        data['details'] = 'URL in excluded list'
        write_data(data_file, data['url'], data['response_code'], data['exception'],
                   data['details'], data['response_length'], data['page_title'],
                   data['url_first_party'])
        return

    # get url and update log data
    response, exception, details = get_url(url, timeout)
    data['exception'] = exception
    data['details'] = details

    # add response details to output
    if response is not None:
        response_content = BeautifulSoup(response.text, 'html.parser')

        data['response_code'] = response.status_code
        data['response_length'] = len(response.text) if response.text else 0
        data['page_title'] = extract_page_title(response_content)

        # check response content for excluded phrases
        excluded_match = contains_excluded_phrases(response_content.body, phrases_to_exclude)
        if excluded_match:
            data['exception'] = 'Excluded Phrase'
            data['details'] = f'Response content contains excluded phrase(s): "{excluded_match}".'

    write_data(data_file, data['url'], data['response_code'], data['exception'],
               data['details'], data['response_length'], data['page_title'], data['url_first_party'])


def main():
    parser = argparse.ArgumentParser(description="Validate URLs from a sitemap.")
    parser.add_argument('--config', default='config.json', help='Path to the configuration file.')
    parser.add_argument('--sitemap_url', help="URL of the sitemap to validate.")
    args = parser.parse_args()
    config = load_config(args.config)

    # get parameters or set default values
    sitemap_url = args.sitemap_url or config.get('sitemap_url')
    if not sitemap_url:
        print("Error: 'sitemap_url' is required but not provided, either \
              in the configuration file or via the command line.")
        sys.exit(1)
    urls_to_exclude = config.get('urls_to_exclude', [])
    phrases_to_exclude = config.get('phrases_to_exclude', [])
    first_party_domains = config.get('first_party_domains', [extract_domain(sitemap_url)])
    request_timeout = config.get('timeout', 10)
    data_file = config.get('data_file_name', 'sitemap_link_validation.csv')

    with open(data_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Response Code', 'Exception', 'Details', 'Response Length',
                        'Page Title', 'First Party'])

    sitemap_response, exception, details = get_url(sitemap_url, request_timeout)
    if sitemap_response:
        urls = parse_sitemap(sitemap_response.text)
        for url in urls:
            validate_url(url, urls_to_exclude, phrases_to_exclude, first_party_domains, 
                         data_file, request_timeout)


if __name__ == '__main__':
    main()
