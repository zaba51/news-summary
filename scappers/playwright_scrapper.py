from playwright.sync_api import sync_playwright
from readability import Document
from bs4 import BeautifulSoup
import time

headless = False

def extract_article_text(url: str, timeout=10000) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        print("Page loaded")
        time.sleep(2)
        try:
            cookie_button_selectors = [
                'button:has-text("Akceptuj")',
                'div.tvp-covl__ab',
                'button:has-text("Accept")',
                'button:has-text("Przejdź")',
                'button:has-text("PRZEJDŹ")',
                'button.cookie-consent__agree',
                'button#onetrust-accept-btn-handler',
                '.js-accept-cookies'
            ]
            for selector in cookie_button_selectors:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    time.sleep(1)
                    break
        except Exception as e:
            print("Nie znaleziono przycisku cookies:", e)       

        html = page.content()
        browser.close()

    doc = Document(html)
    article_html = doc.summary()

    soup = BeautifulSoup(article_html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup.get_text(separator=" ", strip=True)
