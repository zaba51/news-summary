import nltk
import morfeusz2
morf = morfeusz2.Morfeusz()

import requests
from bs4 import BeautifulSoup

nltk.download("stopwords")
nltk.download('punkt_tab')

def scrape_text_from_url(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        h1_title = soup.find('h1', class_='title').get_text() if soup.find('h1', class_='title') else 'No title found'
        p_lead = soup.find('p', class_='lead').get_text() if soup.find('p', class_='lead') else 'No lead found'
        div_content_parts = soup.find('div', class_='contentparts')
        p_content_parts = []
        if div_content_parts:
            for p in div_content_parts.find_all('p', class_='contentpart--text'):
                text = p.get_text()
                if '\xa0' not in text and 'ZOBACZ WIDEO' not in text and not (p.find('a') and text == p.find('a').get_text()):
                    p_content_parts.append(text)
        return h1_title, p_lead, p_content_parts
    else:
        return None, 'No title found', 'No lead found'