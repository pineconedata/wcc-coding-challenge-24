import csv
import requests
from bs4 import BeautifulSoup


def log_request_info(url, response_code, timed_out, exception, response_length, log_file):
    with open(log_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url, response_code, timed_out, exception, response_length])


def get_url(url, log_file, timeout=10):
    try:
        print(f'Retrieving page from {url}')
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        print(f'Retrieved page from {url}')
        response_length = len(response.text) if response.text else 0
        return response.status_code, False, None, response_length, response.text
    except requests.exceptions.Timeout:
        print(f'Error: The request to {url} timed out.')
        return None, True, 'Timeout', 0, None
    except requests.exceptions.RequestException as e:
        print(f'Error: Failed to fetch sitemap from {url}. Details: {e}')
        return None, False, str(e), 0, None


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


def is_url_excluded(url, urls_to_exclude, log_file):
    if url in urls_to_exclude:
        print(f'Skipping {url} as it is in the excluded list.')
        return True
    return False


def contains_excluded_phrases(response_content, phrases_to_exclude):
    for phrase in phrases_to_exclude:
        if phrase.lower() in response_content.lower():
            print(f'Excluded phrase {phrase} found in page.')
            return True
    return False


def validate_url(url, urls_to_exclude, phrases_to_exclude, log_file, timeout):
    # set initial log data
    log_data = {
        'url': url,
        'response_code': None,
        'timed_out': False,
        'exception': None,
        'response_length': 0,
        'skip_reason': None
    }

    # if url is excluded, log and return early
    if is_url_excluded(url, urls_to_exclude, log_file):
        log_data['exception'] = 'Excluded URL'
        log_data['skip_reason'] = 'URL in excluded list'
        log_request_info(log_data['url'], log_data['response_code'], log_data['timed_out'],
                         log_data['exception'], log_data['response_length'], log_file)
        return

    # get url and update log data
    response_code, timed_out, exception, response_length, response_content = get_url(url, log_file, timeout)
    log_data['response_code'] = response_code
    log_data['timed_out'] = timed_out
    log_data['exception'] = exception
    log_data['response_length'] = response_length

    # check response content for excluded phrases
    if response_content is not None:
        if contains_excluded_phrases(response_content, phrases_to_exclude):
            log_data['exception'] = 'Excluded Phrase'
            log_data['skip_reason'] = 'Response content contains excluded phrase.'
            return

    log_request_info(log_data['url'], log_data['response_code'], log_data['timed_out'], log_data['exception'], log_data['response_length'], log_file)


def main():
    sitemap_url = 'https://www.pineconedata.com/sitemap.xml'
    urls_to_exclude = ['https://www.pineconedata.com/404', 'https://www.pineconedata.com/404.html']
    phrases_to_exclude = ['this page doesn\'t exist', 'it is broken']
    request_timeout = 10
    log_file = 'request_log.csv'

    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Response Code', 'Timeout', 'Exception', 'Response Length'])

    response_code, timed_out, exception, response_length, sitemap_content = get_url(sitemap_url, log_file, request_timeout)
    if sitemap_content:
        urls = parse_sitemap(sitemap_content)
        for url in urls:
            validate_url(url, urls_to_exclude, phrases_to_exclude, log_file, request_timeout)


if __name__ == '__main__':
    main()
