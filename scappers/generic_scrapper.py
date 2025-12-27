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

def scrape_text_from_content(content: str,
                             title_class: str = TITLE_CLASS,
                             lead_class: str = LEAD_CLASS,
                             part_class: str = PART_CLASS,
                             paragraph_class: str = PARAGRAPH_CLASS):
    """Same behavior as `scrape_text_from_url` but accepts HTML `content` and
    optional CSS class names to override defaults.
    """
    soup = BeautifulSoup(content, 'html.parser')
    h1_title = soup.find('h1', class_= title_class).get_text() if soup.find('h1', class_= title_class) else None
    p_lead = soup.find('p', class_=lead_class).get_text() if soup.find('p', class_=lead_class) else 'No lead found'
    div_content_parts = soup.find('div', class_=part_class)
    p_content_parts = []
    if div_content_parts:
        for p in div_content_parts.find_all('p', class_=paragraph_class):
            text = p.get_text()
            if '\xa0' not in text and 'ZOBACZ WIDEO' not in text and not (p.find('a') and text == p.find('a').get_text()):
                p_content_parts.append(text)
    return h1_title + " " + p_lead + " " + " ".join(p_content_parts)