from scrapper import scrape_text_from_url
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import re
import os

def _get_pipeline(model_name):
    local_model_dir = os.path.join("models", model_name.replace("/", "_"))
    
    try:
        if not os.path.exists(local_model_dir):
            print(f"Model nie znaleziony lokalnie, pobieram {model_name}...")
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            os.makedirs(local_model_dir, exist_ok=True)
            model.save_pretrained(local_model_dir)
            tokenizer.save_pretrained(local_model_dir)
        else:
            print(f"Ładuję model lokalnie z {local_model_dir}...")
            model = AutoModelForSeq2SeqLM.from_pretrained(local_model_dir)
            tokenizer = AutoTokenizer.from_pretrained(local_model_dir)

        return pipeline("summarization", model=model, tokenizer=tokenizer)
    except Exception as e:
        raise


def sanitize_text(text: str) -> str:
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'\S+@\S+', ' ', text)
    text = re.sub(r'(\b[\w\-.]+(?:\.[a-z]{2,})(?:\.[a-z]{2,})*\b)(?:\s+\1)+', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'(\b\w+\b(?:\s+\b\w+\b))(?:\s+\1){2,}', r'\1', text)
    text = re.sub(r'\b(\w+)(?:\s+\1){2,}', r'\1', text, flags=re.IGNORECASE)
    text = ' '.join(text.split())
    return text

def get_summary(raw_text, model_name: str, max_length: int, min_length: int = 200) -> str:
    try:
        if isinstance(raw_text, (list, tuple)):
            raw_text = " ".join([str(x) for x in raw_text if x])
        raw_text = (raw_text or "").strip()
        if not raw_text:
            return "Brak tekstu do streszczenia."

        text = sanitize_text(raw_text)

        try:
            summarizer = _get_pipeline(model_name)
        except Exception as e:
            return f"Błąd inicjalizacji modelu summarization ({model_name}): {e}"

        target_max_tokens = max(50, int(max_length / 4))
        target_min_tokens = max(10, int(min_length / 4))
        if target_min_tokens >= target_max_tokens:
            target_min_tokens = max(5, target_max_tokens - 1)

        max_chunk_chars = 1000
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
