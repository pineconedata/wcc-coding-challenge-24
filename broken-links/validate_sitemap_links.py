import re
import csv
import sys
import json
import logging
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urlparse


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


def write_data(data_file, url, response_code, exception, details, response_length,
               page_title, url_first_party, link_text, source_url):
    """Write the results to the CSV file."""
    with open(data_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url, response_code, exception, details, response_length,
                         page_title, url_first_party, link_text, source_url])


def load_config(config_file):
    """Load the configuration details from a JSON file."""
    with open(config_file, 'r') as f:
        return json.load(f)


def get_url(url, timeout=10):
    """Send a GET request to the URL with the specified timeout."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response, None, None
    except requests.exceptions.Timeout as e:
        error_details = f'The request to {url} exceeded the threshold of {timeout}'
        logging.error(f'{error_details}')
        return e.response, 'Timeout', error_details
    except requests.exceptions.HTTPError as e:
        error_details = f'HTTPError {e.response.status_code} - {e.response.reason}'
        logging.error(f'{error_details} at {url}')
        return e.response, 'HTTPError', error_details
    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to fetch page from {url}. Details: {e}')
        return e.response, 'RequestException', str(e)


def parse_sitemap(sitemap_content):
    """Parse the sitemap XML content and return a list of URLs."""
    try:
        logging.info('Parsing sitemap content...')
        sitemap_content = sitemap_content.text
        soup = BeautifulSoup(sitemap_content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        logging.info(f'Parsed sitemap content. Found {len(urls)} URLs.')
        if not urls:
            logging.info('No URLs found in the sitemap content.')
        return urls
    except Exception as e:
        logging.error(f'Failed to parse the sitemap XML. Details: {e}')
        return []


def extract_domain(url):
    """Extract the domain from the given URL."""
    try:
        parsed_url = urlparse(url)
        return parsed_url.netloc
    except Exception as e:
        logging.error(f'Failed extract domain from the URL. Details: {e}')
        return url


def is_url_first_party(url, first_party_domains):
    """Determine if the URL is first-party (True) or third-party (False)
    based on first_party_domains list."""
    try:
        domain = extract_domain(url)
        return domain in first_party_domains
    except Exception as e:
        logging.error(f'Failed to check if url is in the excluded list. Details: {e}')
        return None


def is_url_excluded(url, urls_to_exclude):
    """Check if the URL is in the exclusion list."""
    try:
        exclude_patterns = [re.compile(pattern) for pattern in urls_to_exclude]
        matched_url = [pattern.search(url) for pattern in exclude_patterns if pattern.search(url)]
        if matched_url:
            logging.info(f'Skipping {url} as it matches pattern(s) {matched_url} in the excluded list.')
            return True
        return False
    except Exception as e:
        logging.error(f'Failed to check if URL is in the excluded list. Details: {e}')
        return None


def contains_excluded_phrases(content, phrases_to_exclude):
    """Check if the content contains any of the excluded phrases."""
    try:
        content = content.body
        matched_phrases = [phrase for phrase in phrases_to_exclude
                           if re.search(phrase, content.get_text(), re.IGNORECASE)]

        if matched_phrases:
            logging.info(f'Excluded phrase(s) "{matched_phrases}" found in page.')
            return matched_phrases
        return False
    except Exception as e:
        logging.error(f'Failed to check if content contains excluded phrases. Details: {e}')
        return None


def extract_page_title(content):
    """Extract the page title from the HTML content."""
    try:
        title_tag = content.find('title')
        return title_tag.text if title_tag else None
    except Exception as e:
        logging.error(f'Failed to extract page title. Details: {e}')
        return None


def extract_urls_from_content(content):
    """Extract all URLs and their link text from the HTML content using BeautifulSoup."""
    try:
        content = content.body
        links = {(a_tag['href'], a_tag.get_text(strip=True))
                for a_tag in content.find_all('a', href=True)
                if a_tag['href'].startswith('http')}
        return list(links)
    except Exception as e:
        logging.error(f'Failed to extract additional URLs. Details: {e}')
        return []


def validate_url(url, urls_to_exclude, phrases_to_exclude, first_party_domains,
                 timeout, extract_urls):
    """Validate the URL by checking its status, title, and content for exclusions."""
    logging.info(f'Validating URL at {url}')
    data = {
        'url': url,
        'response_code': None,
        'exception': None,
        'details': None,
        'response_length': 0,
        'page_title': None,
        'url_first_party': None,
        'additional_urls': []
    }

    # determine if the URL is first-party or third-party
    data['url_first_party'] = is_url_first_party(url, first_party_domains)

    # if url is excluded, log and return early
    if is_url_excluded(url, urls_to_exclude):
        data['exception'] = 'Excluded URL'
        data['details'] = 'Skipped URL as it matched pattern(s) in the excluded URL list.'
        return data

    # get url and update log data
    response, exception, details = get_url(url, timeout)
    data['exception'] = exception
    data['details'] = details

    # add response details to output
    if response is not None and response.text:
        response_content = BeautifulSoup(response.text, 'html.parser')

        data['response_code'] = response.status_code
        data['response_length'] = len(response.text) if response.text else 0
        data['page_title'] = extract_page_title(response_content)

        # check response content for excluded phrases
        excluded_match = contains_excluded_phrases(response_content, phrases_to_exclude)
        if excluded_match:
            data['exception'] = 'Excluded Phrase'
            data['details'] = f'Response content contains excluded phrase(s): "{excluded_match}".'

        # extract additional URLs from response content
        if extract_urls:
            data['additional_urls'] = extract_urls_from_content(response_content)

    return data


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Validate URLs from a sitemap.")
    parser.add_argument('--config', default='config.json', help='Path to the configuration file.')
    parser.add_argument('--sitemap_url', help="URL of the sitemap to validate.")
    args = parser.parse_args()
    config = load_config(args.config)

    sitemap_url = args.sitemap_url or config.get('sitemap_url')
    if not sitemap_url:
        logging.error("Error: 'sitemap_url' is required but not provided, either \
                      in the configuration file or via the command line.")
        sys.exit(1)

    urls_to_exclude = config.get('urls_to_exclude', [])
    phrases_to_exclude = config.get('phrases_to_exclude', [])
    first_party_domains = config.get('first_party_domains', [extract_domain(sitemap_url)])
    request_timeout = config.get('timeout', 10)
    data_file = config.get('data_file', 'sitemap_link_validation.csv')
    extract_urls = config.get('extract_additional_urls', False)
    all_additional_urls = set()

    # initialize CSV file with headers
    with open(data_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Response Code', 'Exception', 'Details', 'Response Length',
                        'Page Title', 'First Party', 'Link Text', 'Source URL'])

    sitemap_response, exception, details = get_url(sitemap_url, request_timeout)
    if sitemap_response:
        urls = parse_sitemap(sitemap_response)
        for url in urls:
            data = validate_url(url, urls_to_exclude, phrases_to_exclude, first_party_domains, 
                                request_timeout, extract_urls)
            additional_urls = data.pop('additional_urls')
            data['link_text'] = url
            data['source_url'] = sitemap_url
            write_data(data_file, **data)
            if additional_urls:
                additional_urls = [(additional_url, link_text, url) for additional_url,
                                   link_text in additional_urls]
                all_additional_urls.update(additional_urls)
        # after processing sitemap URLs, update and validate the additional URLs
        if all_additional_urls:
            all_additional_urls = [(url, link_text, source_url) for url, link_text, source_url
                                   in all_additional_urls if url not in urls]
            # combine link_text and source_url values for duplicate URLs
            url_dict = {}
            for url, link_text, source_url in all_additional_urls:
                if url not in url_dict:
                    url_dict[url] = {'link_text': [link_text], 'source_url': [source_url]}
                else:
                    url_dict[url]['link_text'].append(link_text)
                    url_dict[url]['source_url'].append(source_url)
            logging.info(f'Extracted {len(url_dict)} additional unique URLs.')
            # process each additional URL
            for url, content in url_dict.items():
                data = validate_url(url, urls_to_exclude, phrases_to_exclude, first_party_domains, 
                                    request_timeout, False)
                additional_urls = data.pop('additional_urls')
                data['link_text'] = content['link_text']
                data['source_url'] = content['source_url']
                write_data(data_file, **data)


if __name__ == '__main__':
    main()
