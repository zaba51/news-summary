from bs4 import BeautifulSoup
import json
import html as _html

def _clean_html_fragment(fragment: str) -> str:
    unescaped = _html.unescape(fragment)
    soup = BeautifulSoup(unescaped, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    return '\n\n'.join([line.strip() for line in text.splitlines() if line.strip()])

def scrape_text_from_content(content: str):
    print("TVP Info scraper called")
    soup = BeautifulSoup(content, 'html.parser')
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