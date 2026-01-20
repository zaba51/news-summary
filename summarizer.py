from scrapper import scrape_text_from_url
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import re
import os
import torch
import time
from sentence_transformers import SentenceTransformer, util
import csv

device = 0 if torch.cuda.is_available() else -1
polish_models = ['airKlizz/mt5-base-wikinewssum-polish']
polish_input_models = ['z-dickson/bart-large-cnn-climate-change-summarization']
max_chunk_chars = 1600
enable_logs = False

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

def translation_pipeline(model_name, input_lang="en"):
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
        input_tokens = len(translation_tokenizer.encode(text_pl))
        if enable_logs:
            print(f"Input text length: {len(text_pl)}, Tokens: {int(input_tokens)}\n")
        kwargs = {"max_length": int(input_tokens * 1.2)} 

        if input_lang=="en":
            input_text = pl_en(text_pl, **kwargs)[0]["translation_text"]
            if enable_logs:
                input_tokens = len(translation_tokenizer.encode(input_text))
                print(f"Translated to English ({len(input_text)} chars), Tokens: {int(input_tokens)}:", input_text[:100], "...\n")
        else:
            input_text = text_pl

        input_tokens = len(summary_tokenizer.encode(input_text))

        gen_kwargs = {
            "max_length": max(50, int(input_tokens * 0.6)),
            "min_length": max(30, int(input_tokens * 0.4)),
            "do_sample": False,
            "num_beams": 4,
            "no_repeat_ngram_size": 3,
            "repetition_penalty": 1.1,
            }

        en_summary = en_summarizer(
            input_text,
            **gen_kwargs
        )[0]["summary_text"]

        output_tokens = len(translation_tokenizer.encode(en_summary))
        if enable_logs:
            print(f"English summary ({len(en_summary)} chars), Tokens: {int(output_tokens)}:", en_summary[:100], "...\n")
        kwargs = {"max_length": int(output_tokens * 1.2)}

        pl_summary = en_pl(en_summary, **kwargs)[0]["translation_text"]
        return [{"summary_text": pl_summary}]

    return summary, summary_tokenizer


def get_pipeline(model_name):
    if model_name in polish_models:
        model, tokenizer = load_model(model_name)
        return pipeline("summarization", model=model, tokenizer=tokenizer, device=device), tokenizer
    else:
        return translation_pipeline(model_name, "pl" if model_name in polish_input_models else "en")

def count_tokens(tokenizer, text):
    return len(tokenizer.encode(text, truncation=False))

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

        print("Długość tekstu wejściowego (znaki):", len(raw_text))

        text = sanitize_text(raw_text)
        summarizer, tokenizer = get_pipeline(model_name)

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

        start_time = time.time()
        prefix = ""

        summaries = []
        for ch in chunks:
            input_tokens = count_tokens(tokenizer, prefix + ch)

            max_len = max(60, int(input_tokens * 0.6))
            min_len = max(40, int(input_tokens * 0.4))

            if min_len >= max_len:
                min_len = max(30, max_len - 10)

            gen_kwargs = {
                "max_length": max_len,
                "min_length": min_len,
                "do_sample": False,
                "num_beams": 4,
                "no_repeat_ngram_size": 3,
                "repetition_penalty": 1.1,
            }

            out = summarizer(prefix + ch, **gen_kwargs)
            summaries.append(out[0]["summary_text"])

        combined = " ".join(summaries)
        combined_len = len(combined)

        elapsed = time.time() - start_time

        if enable_logs:
            print(f"Długość po ETAPIE 1 (znaki): {combined_len}\n")
            print(f"Liczba chunków: {len(summaries)}")
            print(f"Combined summary preview:\n{combined[:300]}...\n")

        if combined_len <= max_length:
            result = combined.strip()

        else:
            embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

            chunk_embeddings = embed_model.encode(summaries, convert_to_tensor=True)
            
            final_chunks = []
            selected_indices = set()
            current_len = 0

            # Centroid całego dokumentu
            doc_embedding = torch.mean(chunk_embeddings, dim=0, keepdim=True)

            # MMR loop
            for _ in range(len(summaries)):
                # Chunk z maksymalnym similarity do doc_embedding
                scores = util.cos_sim(chunk_embeddings, doc_embedding).squeeze(1)
                for idx in selected_indices:
                    scores[idx] = -1
                
                best_idx = int(scores.argmax())
                candidate = summaries[best_idx]
                candidate_len = len(candidate)
                remaining_space = max_length - current_len

                if current_len + candidate_len > max_length:
                    cut_pos = candidate.rfind('. ', 0, remaining_space)
                    if cut_pos == -1:
                        # Brak kropki, przycinamy do limitu
                        candidate = candidate[:remaining_space].rstrip()
                    else:
                        # Przycinamy do ostatniej kropki
                        candidate = candidate[:cut_pos + 1].rstrip()
                    final_chunks.append(candidate)
                    current_len += len(candidate)
                    break 
                
                final_chunks.append(candidate)
                selected_indices.add(best_idx)
                current_len += candidate_len

                if current_len >= min_length:
                    break

                result = " ".join(final_chunks).strip()

                print(f"Długość po ETAPIE 2 (MMR ranking) (znaki): {len(result)}\n")


        result = re.sub(r'(\b\w+\b(?:\s+\b\w+\b))(?:\s+\1){2,}', r'\1', result)
        result = re.sub(r'\b(\w+)(?:\s+\1){2,}', r'\1', result, flags=re.IGNORECASE)

        print(f"Czas od chunkowania do końca funkcji: {elapsed:.2f} s")

        return result, elapsed

    except Exception as e:
        return f"Nieznany błąd: {e}"
