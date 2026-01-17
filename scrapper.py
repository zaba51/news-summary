import re
import requests

from scappers import tvpinfo, sportowefakty, generic_scrapper, playwright_scrapper

def scrape_text_from_url(url: str):
    return playwright_scrapper.extract_article_text(url)

    try:
        response = requests.get(url)
    except Exception:
        return None

    if response.status_code != 200:
        return None

    content = response.content

    # tvp.info at the start of the host (allow optional scheme)
    if re.search(r'^(?:https?://)?(?:www\.)?tvp\.info', url):
        return tvpinfo.scrape_text_from_content(content)

    # contains sportowefakty anywhere in the URL
    if re.search(r'sportowefakty', url):
        return sportowefakty.scrape_text_from_content(content)

    # fallback to generic
    return generic_scrapper.scrape_text_from_content(content)