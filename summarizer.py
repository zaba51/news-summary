from transformers import pipeline
from scrapper import scrape_text_from_url





def get_summary(url: str, max_length: int) -> str:
    try:
        raw_text = scrape_text_from_url(url)

    except ConnectionError as e:
        return f"Błąd połączenia: {e}"
    except ValueError as e:
        return f"Błąd danych: {e}"
    except Exception as e:
        return f"Nieznany błąd: {e}"