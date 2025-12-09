from transformers import pipeline
from scrapper import scrape_text_from_url





def get_summary(raw_text: str, max_length: int) -> str:
    try:
        print("Raw_text", raw_text)
        return raw_text

    except ConnectionError as e:
        return f"Błąd połączenia: {e}"
    except ValueError as e:
        return f"Błąd danych: {e}"
    except Exception as e:
        return f"Nieznany błąd: {e}"