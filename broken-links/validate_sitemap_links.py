import csv
import requests
from bs4 import BeautifulSoup


def write_data(data_file, url, response_code, timed_out, exception, response_length):
    with open(data_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url, response_code, timed_out, exception, response_length])


def get_url(url, timeout=10):
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


def is_url_excluded(url, urls_to_exclude):
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


def validate_url(url, urls_to_exclude, phrases_to_exclude, data_file, timeout):
    # set initial values
    data = {
        'url': url,
        'response_code': None,
        'timed_out': False,
        'exception': None,
        'response_length': 0,
        'skip_reason': None
    }

    # if url is excluded, log and return early
    if is_url_excluded(url, urls_to_exclude):
        data['exception'] = 'Excluded URL'
        data['skip_reason'] = 'URL in excluded list'
        write_data(data_file, data['url'], data['response_code'], data['timed_out'],
                         data['exception'], data['response_length'])
        return

    # get url and update log data
    response_code, timed_out, exception, response_length, response_content = get_url(url, timeout)
    data['response_code'] = response_code
    data['timed_out'] = timed_out
    data['exception'] = exception
    data['response_length'] = response_length

    # check response content for excluded phrases
    if response_content is not None:
        if contains_excluded_phrases(response_content, phrases_to_exclude):
            data['exception'] = 'Excluded Phrase'
            data['skip_reason'] = 'Response content contains excluded phrase.'
            return

    write_data(data_file, data['url'], data['response_code'], data['timed_out'], data['exception'], data['response_length'])


def main():
    sitemap_url = 'https://www.pineconedata.com/sitemap.xml'
    urls_to_exclude = ['https://www.pineconedata.com/404', 'https://www.pineconedata.com/404.html']
    phrases_to_exclude = ['this page doesn\'t exist', 'it is broken']
    request_timeout = 10
    data_file = 'request_log.csv'

    with open(data_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Response Code', 'Timeout', 'Exception', 'Response Length'])

    response_code, timed_out, exception, response_length, sitemap_content = get_url(sitemap_url, request_timeout)
    if sitemap_content:
        urls = parse_sitemap(sitemap_content)
        for url in urls:
            validate_url(url, urls_to_exclude, phrases_to_exclude, data_file, request_timeout)


if __name__ == '__main__':
    main()
