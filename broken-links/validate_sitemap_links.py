import requests
from bs4 import BeautifulSoup


def get_sitemap(sitemap_url):
    try:
        print(f'Retrieving sitemap from {sitemap_url}')
        response = requests.get(sitemap_url, timeout=sitemap_timeout)
        response.raise_for_status()
        print(f'Retrieved sitemap from {sitemap_url}')
        return response.text
    except requests.exceptions.Timeout:
        print(f'Error: The request to {sitemap_url} timed out.')
        return None
    except requests.exceptions.RequestException as e:
        print(f'Error: Failed to fetch sitemap from {sitemap_url}. Details: {e}')
        return None


def parse_sitemap(sitemap_content):
    try:
        print('Parsing sitemap content.')
        soup = BeautifulSoup(sitemap_content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        print(f'Parsed sitemap content. Found {len(urls)} URLs.')
        return urls
    except Exception as e:
        print(f'Error: Failed to parse the sitemap XML. Details: {e}')
        return []


sitemap_url = 'https://www.pineconedata.com/sitemap.xml'
sitemap_timeout = 10
sitemap_content = get_sitemap(sitemap_url)
parse_sitemap(sitemap_content)
