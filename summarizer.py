from scrapper import scrape_text_from_url
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import re
import os
import torch

device = 0 if torch.cuda.is_available() else -1
polish_models = ['airKlizz/mt5-base-wikinewssum-polish', 'z-dickson/bart-large-cnn-climate-change-summarization']
max_chunk_chars = 1600

def load_model(model_name):
    local_model_dir = os.path.join("models", model_name.replace("/", "_"))

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

    return model, tokenizer

def translation_pipeline(model_name):
    translation_model, translation_tokenizer = load_model("facebook/nllb-200-distilled-600M")
    summary_model, summary_tokenizer = load_model(model_name)
    
    pl_en = pipeline(
        "translation",
        model=translation_model,
        tokenizer=translation_tokenizer,
        src_lang="pol_Latn",
        tgt_lang="eng_Latn",
        device=device
    )
    en_summarizer = pipeline(
        "summarization",
        model=summary_model,
        tokenizer=summary_tokenizer,
        device=device
    )
    en_pl = pipeline(
        "translation",
        model=translation_model,
        tokenizer=translation_tokenizer,
        src_lang="eng_Latn",
        tgt_lang="pol_Latn",
        device=device
    )

    def summary(text_pl, **gen_kwargs):
        print("Input text length:", len(text_pl))
        input_tokens = len(translation_tokenizer.encode(text_pl))
        # gen_kwargs = {"max_length": int(input_tokens * 1.2)} 
        gen_kwargs = {"max_length":1024} 

        en_text = pl_en(text_pl, **gen_kwargs)[0]["translation_text"]
        print(f"Translated to English ({len(en_text)} chars):", en_text[:100], "...")
        en_summary = en_summarizer(
            en_text,
            **gen_kwargs
        )[0]["summary_text"]
        print(f"English summary ({len(en_summary)} chars):", en_summary[:100], "...")
        output_tokens = len(translation_tokenizer.encode(en_summary))
        # gen_kwargs = {"max_length": int(output_tokens * 1.2)}
        gen_kwargs = {"max_length": 1024}

        pl_summary = en_pl(en_summary, **gen_kwargs)[0]["translation_text"]
        return [{"summary_text": pl_summary}]

    return summary


def get_pipeline(model_name):
    if model_name in polish_models:
        model, tokenizer = load_model(model_name)
        return pipeline("summarization", model=model, tokenizer=tokenizer, device=device)
    else:
        return translation_pipeline(model_name)


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
        raw_text = (raw_text or "").strip()
        if not raw_text:
            return "Brak tekstu do streszczenia."

        text = sanitize_text(raw_text)
        summarizer = get_pipeline(model_name)

        target_max_tokens = max(50, int(max_length / 4))
        target_min_tokens = max(10, int(min_length / 4))

        if target_min_tokens >= target_max_tokens:
            target_min_tokens = max(5, target_max_tokens - 1)

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

        # gen_kwargs = {
        #     "max_length": 220,
        #     "min_length": 120,
        #     "do_sample": True,
        #     "top_p": 0.9,
        #     "temperature": 0.8,
        #     "no_repeat_ngram_size": 3,
        # }
        gen_kwargs = {
            "max_length": 220,
            "min_length": 120,
            "do_sample": True,
            "num_beams": 4,
            "no_repeat_ngram_size": 3,
            "repetition_penalty": 1.1,
        }

        prefix = "summarize: " if ("t5" in model_name or "mt5" in model_name) else ""

        summaries = []
        for ch in chunks:
            out = summarizer(
                prefix + ch,
                **gen_kwargs
            )
            summaries.append(out[0]["summary_text"])

        if not summaries:
            return "Nie udało się wygenerować streszczenia."
        
        for s in summaries:
            print(f"Summary chunk: {s}\n\n")

        # final length
        gen_kwargs = {
            "max_length": int(target_max_tokens),
            "min_length": int(target_min_tokens),
            # "do_sample": False,
            # "num_beams": 4,
            # "no_repeat_ngram_size": 3,
            # "early_stopping": True,
            # "repetition_penalty": 2.0,
            # "do_sample": False,
            # "top_p": 0.9,
            # "temperature": 0.8,
            # "no_repeat_ngram_size": 3,
            "do_sample": False,
            "num_beams": 5,
            "no_repeat_ngram_size": 3,
        }

        combined = " ".join(summaries)
        final_out = summarizer(prefix + combined, **gen_kwargs)
        result = final_out[0]["summary_text"].strip()

        result = re.sub(r'(\b\w+\b(?:\s+\b\w+\b))(?:\s+\1){2,}', r'\1', result)
        result = re.sub(r'\b(\w+)(?:\s+\1){2,}', r'\1', result, flags=re.IGNORECASE)

        return result

    except Exception as e:
        return f"Nieznany błąd: {e}"
