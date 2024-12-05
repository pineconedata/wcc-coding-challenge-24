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
        log_request_info(url, response.status_code, False, None, response_length, log_file)
        return response.text
    except requests.exceptions.Timeout:
        print(f'Error: The request to {url} timed out.')
        log_request_info(url, None, True, 'Timeout', 0, log_file)
        return None
    except requests.exceptions.RequestException as e:
        print(f'Error: Failed to fetch sitemap from {url}. Details: {e}')
        log_request_info(url, None, False, str(e), 0, log_file)
        return None


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
        print(f'Skipping {url} as it is in the excluded list')
        log_request_info(url, None, False, 'URL in excluded list', 0, log_file)
        return True
    return False


def validate_url(url, urls_to_exclude, log_file, timeout):
    if is_url_excluded(url, urls_to_exclude, log_file):
        return
    response_content = get_url(url, log_file, timeout)
    if response_content is not None:
        print(f'Checking response content for {url}')


def main():
    sitemap_url = 'https://www.pineconedata.com/sitemap.xml'
    urls_to_exclude = ['https://www.pineconedata.com/404', 'https://www.pineconedata.com/404.html']
    request_timeout = 10
    log_file = 'request_log.csv'

    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Response Code', 'Timeout', 'Exception', 'Response Length'])

    sitemap_content = get_url(sitemap_url, log_file, request_timeout)
    if sitemap_content:
        urls = parse_sitemap(sitemap_content)
        for url in urls:
            validate_url(url, urls_to_exclude, log_file, request_timeout)


if __name__ == '__main__':
    main()
