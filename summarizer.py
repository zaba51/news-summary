from scrapper import scrape_text_from_url
from transformers import pipeline, MBartForConditionalGeneration, MBart50TokenizerFast
import re

model_name = "facebook/mbart-large-50"
# model_name = "google/mt5-small"

# cache the pipeline to avoid repeated initialisation
_CACHED_SUMMARIZER = None

def _get_pipeline():
    global _CACHED_SUMMARIZER
    if _CACHED_SUMMARIZER is None:
        try:
            _CACHED_SUMMARIZER = pipeline("summarization", model=model_name, tokenizer=model_name)
        except Exception as e:
            raise
    return _CACHED_SUMMARIZER

def get_summary(raw_text, max_length: int, min_length: int = 200) -> str:
    try:
        print("="*80)
        print(raw_text)
        print("="*80)
        # normalizacja wejścia
        if isinstance(raw_text, (list, tuple)):
            raw_text = " ".join([str(x) for x in raw_text if x])
        raw_text = (raw_text or "").strip()
        if not raw_text:
            return "Brak tekstu do streszczenia."

        # basic sanitization: remove urls/emails and collapse repeated domains/words
        text = raw_text
        text = re.sub(r'https?://\S+|www\.\S+', ' ', text)         # remove urls
        text = re.sub(r'\S+@\S+', ' ', text)                      # remove emails
        # collapse repeated domain-like tokens: example.com example.com -> example.com
        text = re.sub(r'(\b[\w\-.]+(?:\.[a-z]{2,})(?:\.[a-z]{2,})*\b)(?:\s+\1)+', r'\1', text, flags=re.IGNORECASE)
        # collapse repeated word pairs/triples like "A B A B A B..." -> "A B"
        text = re.sub(r'(\b\w+\b(?:\s+\b\w+\b))(?:\s+\1){2,}', r'\1', text)
        # collapse repeated single word occurrences longer than 2 -> single
        text = re.sub(r'\b(\w+)(?:\s+\1){2,}', r'\1', text, flags=re.IGNORECASE)
        text = ' '.join(text.split())

        try:
            summarizer = _get_pipeline()
        except Exception as e:
            return f"Błąd inicjalizacji modelu summarization ({model_name}): {e}"

        # konwersja max/min characters -> przybliżone tokeny (heurystyka)
        target_max_tokens = max(50, int(max_length / 4))
        target_min_tokens = max(10, int(min_length / 4))
        if target_min_tokens >= target_max_tokens:
            target_min_tokens = max(5, target_max_tokens - 1)

        # chunking tekstu na fragmenty ~1000 znaków
        max_chunk_chars = 1000
        # use sanitized 'text' for chunking
        text = text
        chunks = []
        while text:
            if len(text) <= max_chunk_chars:
                chunks.append(text)
                break
            split_pos = text.rfind("\n\n", 0, max_chunk_chars)
            if split_pos <= 0:
                split_pos = text.rfind(". ", 0, max_chunk_chars)
            if split_pos <= 0:
                split_pos = max_chunk_chars
            chunk = text[:split_pos + 1] if split_pos < len(text) else text[:max_chunk_chars]
            chunks.append(chunk.strip())
            text = text[len(chunk):].strip()

        # Use token-aware generation kwargs; avoid both max_length and max_new_tokens together.
        gen_kwargs = {
            "max_new_tokens": int(target_max_tokens),
            "min_length": int(target_min_tokens),
            "do_sample": False,
            "num_beams": 4,
            "no_repeat_ngram_size": 3,
            "early_stopping": True,
            "repetition_penalty": 2.0,
        }

        prefix = "summarize: " if ("t5" in model_name or "mt5" in model_name) else ""

        summaries = []
        for ch in chunks:
            try:
                out = summarizer(prefix + ch, **gen_kwargs)
                if isinstance(out, list) and out and "summary_text" in out[0]:
                    summaries.append(out[0]["summary_text"].strip())
                elif isinstance(out, dict) and "generated_text" in out:
                    summaries.append(out["generated_text"].strip())
                else:
                    summaries.append(str(out).strip())
            except Exception:
                continue

        if not summaries:
            return "Nie udało się wygenerować streszczenia."

        combined = " ".join(summaries)
        if len(summaries) > 1:
            try:
                final_out = summarizer(prefix + combined, **gen_kwargs)
                if isinstance(final_out, list) and final_out and "summary_text" in final_out[0]:
                    result = final_out[0]["summary_text"].strip()
                elif isinstance(final_out, dict) and "generated_text" in final_out:
                    result = final_out["generated_text"].strip()
                else:
                    result = combined
            except Exception:
                result = combined
        else:
            result = combined

        # final cleanup: collapse accidental repeated short sequences in model output
        result = re.sub(r'(\b\w+\b(?:\s+\b\w+\b))(?:\s+\1){2,}', r'\1', result)
        result = re.sub(r'\b(\w+)(?:\s+\1){2,}', r'\1', result, flags=re.IGNORECASE)
        if len(result) > max_length:
            result = result[:max_length].rsplit(" ", 1)[0] + "…"

        return result

    except ConnectionError as e:
        return f"Błąd połączenia: {e}"
    except ValueError as e:
        return f"Błąd danych: {e}"
    except Exception as e:
        return f"Nieznany błąd: {e}"