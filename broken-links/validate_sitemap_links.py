import re
import csv
import requests
from bs4 import BeautifulSoup


def write_data(data_file, url, response_code, exception, details, response_length, page_title):
    with open(data_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url, response_code, exception, details, response_length, page_title])


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


def is_url_excluded(url, urls_to_exclude):
    if url in urls_to_exclude:
        print(f'Skipping {url} as it is in the excluded list.')
        return True
    return False


def contains_excluded_phrases(content, phrases_to_exclude):
    for phrase in phrases_to_exclude:
        if re.search(phrase, content.get_text(), re.IGNORECASE):
            print(f'Excluded phrase "{phrase}" found in page.')
            return phrase
    return False


def extract_page_title(content):
    try:
        title_tag = content.find('title')
        return title_tag.text if title_tag else None
    except Exception as e:
        print(f'Error: Failed to extract page title. Details: {e}')
        return None


def validate_url(url, urls_to_exclude, phrases_to_exclude, data_file, timeout):
    # set initial values
    data = {
        'url': url,
        'response_code': None,
        'exception': None,
        'details': None,
        'response_length': 0,
        'page_title': None
    }

    # if url is excluded, log and return early
    if is_url_excluded(url, urls_to_exclude):
        data['exception'] = 'Excluded URL'
        data['details'] = 'URL in excluded list'
        write_data(data_file, data['url'], data['response_code'], data['exception'],
                   data['details'], data['response_length'], data['page_title'])
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
        excluded_phrase = contains_excluded_phrases(response_content.body, phrases_to_exclude)
        if excluded_phrase:
            data['exception'] = 'Excluded Phrase'
            data['details'] = f'Response content contains an excluded phrase: "{excluded_phrase}".'

    write_data(data_file, data['url'], data['response_code'], data['exception'],
               data['details'], data['response_length'], data['page_title'])


def main():
    sitemap_url = 'https://www.pineconedata.com/sitemap.xml'
    urls_to_exclude = ['https://www.pineconedata.com/404', 'https://www.pineconedata.com/404.html']
    phrases_to_exclude = ["this page doesn't exist", 'it is broken']
    request_timeout = 10
    data_file = 'sitemap_link_validation.csv'

    with open(data_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Response Code', 'Exception', 'Details', 'Response Length',
                        'Page Title'])

    sitemap_response, exception, details = get_url(sitemap_url, request_timeout)
    if sitemap_response:
        urls = parse_sitemap(sitemap_response.text)
        for url in urls:
            validate_url(url, urls_to_exclude, phrases_to_exclude, data_file, request_timeout)


if __name__ == '__main__':
    main()
