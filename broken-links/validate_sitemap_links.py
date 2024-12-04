import requests
from bs4 import BeautifulSoup


def get_url(url, timeout=10):
    try:
        print(f'Retrieving page from {url}')
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        print(f'Retrieved page from {url}')
        return response.text
    except requests.exceptions.Timeout:
        print(f'Error: The request to {url} timed out.')
        return None
    except requests.exceptions.RequestException as e:
        print(f'Error: Failed to fetch sitemap from {url}. Details: {e}')
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


def main():
    sitemap_url = 'https://www.pineconedata.com/sitemap.xml'
    sitemap_timeout = 10

    sitemap_content = get_url(sitemap_url, sitemap_timeout)
    urls = parse_sitemap(sitemap_content)
    print(urls)


if __name__ == '__main__':
    main()
