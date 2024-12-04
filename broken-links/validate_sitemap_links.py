import requests


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
        print(f'Error: Failed to fetch sitemap from {sitemap_url}. Detailed error information: {e}')
        return None


sitemap_url = 'https://www.pineconedata.com/sitemap.xml'
sitemap_timeout = 10
get_sitemap(sitemap_url)
