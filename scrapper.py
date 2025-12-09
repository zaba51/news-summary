import nltk
import morfeusz2
morf = morfeusz2.Morfeusz()

import requests
from bs4 import BeautifulSoup
import json
import html as _html
import time

nltk.download("stopwords")
nltk.download('punkt_tab')

TITLE_CLASS = 'article__header--title'
LEAD_CLASS = 'article__heading'
PART_CLASS = 'article__paragraph-item'
PARAGRAPH_CLASS = ''

def _clean_html_fragment(fragment: str) -> str:
    unescaped = _html.unescape(fragment)
    soup = BeautifulSoup(unescaped, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    return '\n\n'.join([line.strip() for line in text.splitlines() if line.strip()])


def scrape_text_from_url(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        h1_title = soup.find('h1', class_= TITLE_CLASS).get_text() if soup.find('h1', class_= TITLE_CLASS) else None
        if h1_title is not None:
            p_lead = soup.find('p', class_=LEAD_CLASS).get_text() if soup.find('p', class_=LEAD_CLASS) else 'No lead found'
            div_content_parts = soup.find('div', class_=PART_CLASS)
            p_content_parts = []
            if div_content_parts:
                for p in div_content_parts.find_all('p', class_=PARAGRAPH_CLASS):
                    text = p.get_text()
                    if '\xa0' not in text and 'ZOBACZ WIDEO' not in text and not (p.find('a') and text == p.find('a').get_text()):
                        p_content_parts.append(text)
            return h1_title + " " + p_lead + " " + " ".join(p_content_parts)
        else:
            for script in soup.find_all('script', type='application/ld+json'):
                print("Script found")
                try:
                    payload = json.loads(script.string or script.get_text() or '{}')
                    objs = payload if isinstance(payload, list) else [payload]
                    for obj in objs:
                        if not isinstance(obj, dict):
                            print("not instance")
                            continue
                        title = obj.get('headline') or title
                        article_body = obj.get('articleBody') or obj.get('articleBody')
                        if article_body:
                            full_text = _clean_html_fragment(article_body)
                        
                        if full_text:
                            break

                    return title + ". " + full_text
                    
                except Exception:
                    print("Blad")
                    continue
    else:
        return None, 'No title found', 'No lead found'