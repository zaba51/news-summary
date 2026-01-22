import tkinter as tk
from tkinter import ttk, messagebox
from scrapper import scrape_text_from_url
import re
from summarizer import get_summary
import csv
import os

class NewsSummarizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Podsumowawanie wiadomości")
        master.geometry("600x600")

        self.mode_var = tk.StringVar(value="input")
        self.url_var = tk.StringVar()
        self.max_chars_var = tk.StringVar(value="2000")
        self.min_chars_var = tk.StringVar(value="1500")

        self.create_widgets()

    def create_widgets(self):
        mode_frame = ttk.Frame(self.master, padding="8")
        mode_frame.pack(fill='x', padx=10, pady=(10, 2))
        ttk.Radiobutton(mode_frame, text="Wprowadź tekst", variable=self.mode_var, value="input",
                        command=self.update_input_mode).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(mode_frame, text="Url", variable=self.mode_var, value="url",
                        command=self.update_input_mode).pack(side=tk.LEFT)

        self.inputs_container = ttk.Frame(self.master)
        self.inputs_container.pack(fill='x', padx=10, pady=5)

        self.input_frame = ttk.Frame(self.inputs_container, padding="10")
        ttk.Label(self.input_frame, text="Wprowadź swój tekst", anchor='w').pack(fill='x', pady=(0, 2))
        self.input_text = tk.Text(self.input_frame, height=3, wrap='word')
        self.input_text.pack(fill='x', ipady=3)

        self.url_frame = ttk.Frame(self.inputs_container, padding="10")
        ttk.Label(self.url_frame, text="Wklej swój url:", anchor='w').pack(fill='x', pady=(0, 2))
        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.url_var)
        self.url_entry.pack(fill='x', ipady=5)

        self.input_frame.pack(fill='x')

        button_frame = ttk.Frame(self.master, padding="10")
        button_frame.pack(fill='x', padx=10, pady=5)

        config_frame = ttk.Frame(self.master, padding="10")
        config_frame.pack(fill='x', padx=10, pady=5)

        config_frame = ttk.Frame(self.master, padding="10")
        config_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(config_frame, text="Konfiguracja", anchor='w').pack(fill='x', pady=(0, 5))

        max_frame = ttk.Frame(config_frame)
        max_frame.pack(fill='x', pady=2)
        ttk.Label(max_frame, text="Maksymalna liczba znaków (przybliżona):", anchor='w').pack(side=tk.LEFT)
        max_chars_entry = ttk.Entry(max_frame, textvariable=self.max_chars_var, width=10)
        max_chars_entry.pack(side=tk.LEFT, padx=(5,0))

        min_frame = ttk.Frame(config_frame)
        min_frame.pack(fill='x', pady=2)
        ttk.Label(min_frame, text="Minimalna liczba znaków (przybliżona):", anchor='w').pack(side=tk.LEFT)
        min_chars_entry = ttk.Entry(min_frame, textvariable=self.min_chars_var, width=10)
        min_chars_entry.pack(side=tk.LEFT, padx=(5,0))

        self.model_var = tk.StringVar(value="airKlizz/mt5-base-wikinewssum-polish")

        model_frame = ttk.Frame(config_frame)
        model_frame.pack(fill='x', pady=5)

        ttk.Label(model_frame, text="Wybierz model:", anchor='w').pack(side=tk.LEFT)

        example_models = [
            'airKlizz/mt5-base-wikinewssum-polish',
            'z-dickson/bart-large-cnn-climate-change-summarization',
            "csebuetnlp/mT5_multilingual_XLSum",
            "facebook/bart-large-cnn"
        ]

        self.model_combobox = ttk.Combobox(model_frame, textvariable=self.model_var,
                                        values=example_models, state="readonly", width=30)
        self.model_combobox.pack(side=tk.LEFT, padx=(5,0))

        generate_button = ttk.Button(self.master, text="Generuj podsumowanie", command=self.generate_summary_action)
        generate_button.pack(pady=10)

        output_frame = ttk.Frame(self.master, padding="10")
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)

        ttk.Label(output_frame, text="Wynik:", anchor='w').pack(fill='x', pady=(0, 2))

        self.output_text = tk.Text(output_frame, height=10, wrap='word')
        self.output_text.pack(fill='both', expand=True, ipady=5)

    def update_input_mode(self):
        mode = self.mode_var.get()
        if mode == "input":
            try:
                self.url_frame.pack_forget()
            except Exception:
                pass
            if not self.input_frame.winfo_ismapped():
                self.input_frame.pack(fill='x')
        else:
            try:
                self.input_frame.pack_forget()
            except Exception:
                pass
            if not self.url_frame.winfo_ismapped():
                self.url_frame.pack(fill='x')

    def generate_summary_action(self):
        mode = self.mode_var.get()
        max_len_str = self.max_chars_var.get().strip()
        min_len_str = self.min_chars_var.get().strip()
        selected_model = self.model_var.get()

        try:
            max_length = int(max_len_str)
            if max_length <= 0:
                messagebox.showerror("Błąd", "Maksymalna liczba znaków musi być dodatnią liczbą całkowitą.")
                return
        except ValueError:
            messagebox.showerror("Błąd", "Maksymalna liczba znaków musi być liczbą całkowitą.")
            return

        try:
            min_length = int(min_len_str)
            if min_length <= 0:
                messagebox.showerror("Błąd", "Minimalna liczba znaków musi być dodatnią liczbą całkowitą.")
                return
            if min_length > max_length:
                messagebox.showerror("Błąd", "Minimalna liczba znaków nie może być większa niż maksymalna.")
                return
        except ValueError:
            messagebox.showerror("Błąd", "Minimalna liczba znaków musi być liczbą całkowitą.")
            return

        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Trwa generowanie podsumowania... Proszę czekać.")
        self.master.update()

        try:
            if mode == "input":
                text = self.input_text.get("1.0", tk.END).strip()
                if not text:
                    messagebox.showerror("Błąd", "Proszę wprowadzić tekst wejściowy.")
                    return
            else:
                url = self.url_var.get().strip()
                if not url:
                    messagebox.showerror("Błąd", "Proszę podać URL artykułu.")
                    return
                scraped = scrape_text_from_url(url)
                if isinstance(scraped, (list, tuple)):
                    text = " ".join([s for s in scraped if s])
                else:
                    text = scraped or ""

            summary, time = get_summary(text, selected_model, max_length, min_length)
            
            csv_filename = "summary_log.csv"
            file_exists = os.path.isfile(csv_filename)
            with open(csv_filename, mode="a", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["text_length", "model_name", "summary_length", "elapsed_s", "summary_text"])
                writer.writerow([len(text), selected_model, len(summary), time, summary])

            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, summary)

        except Exception as e:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"Wystąpił błąd podczas generowania podsumowania: {e}")
            messagebox.showerror("Błąd operacji", f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = NewsSummarizerApp(root)
    root.mainloop()