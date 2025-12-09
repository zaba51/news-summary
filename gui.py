import tkinter as tk
from tkinter import ttk, messagebox
from scrapper import scrape_text_from_url

try:
    from summarizer import get_summary
except ImportError:
    def get_summary(url, max_length):
        print(f"PLACEHOLDER")
        return "PLACEHOLDER"


class NewsSummarizerApp:
    def __init__(self, master):
        self.master = master
        master.title("News Summarizer")
        master.geometry("600x450")

        self.mode_var = tk.StringVar(value="input")  # "input" or "url"
        self.url_var = tk.StringVar()
        self.max_chars_var = tk.StringVar(value="500")

        self.create_widgets()

    def create_widgets(self):
        # mode selection (Input text / Url)
        mode_frame = ttk.Frame(self.master, padding="8")
        mode_frame.pack(fill='x', padx=10, pady=(10, 2))
        ttk.Radiobutton(mode_frame, text="Input text", variable=self.mode_var, value="input",
                        command=self.update_input_mode).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(mode_frame, text="Url", variable=self.mode_var, value="url",
                        command=self.update_input_mode).pack(side=tk.LEFT)

        # inputs container placed directly under mode_frame so shown fields stay there
        self.inputs_container = ttk.Frame(self.master)
        self.inputs_container.pack(fill='x', padx=10, pady=5)

        # Input text frame (default visible) - child of inputs_container
        self.input_frame = ttk.Frame(self.inputs_container, padding="10")
        ttk.Label(self.input_frame, text="Input your text", anchor='w').pack(fill='x', pady=(0, 2))
        self.input_text = tk.Text(self.input_frame, height=3, wrap='word')
        self.input_text.pack(fill='x', ipady=3)

        # Url frame (hidden by default) - child of inputs_container
        self.url_frame = ttk.Frame(self.inputs_container, padding="10")
        ttk.Label(self.url_frame, text="Paste your url here:", anchor='w').pack(fill='x', pady=(0, 2))
        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.url_var)
        self.url_entry.pack(fill='x', ipady=5)

        # pack only the active input frame initially inside inputs_container
        self.input_frame.pack(fill='x')

        # remaining UI (config, buttons, output) - reuse existing layout
        button_frame = ttk.Frame(self.master, padding="10")
        button_frame.pack(fill='x', padx=10, pady=5)

        config_frame = ttk.Frame(self.master, padding="10")
        config_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(config_frame, text="Summary config", anchor='w').pack(fill='x', pady=(0, 2))

        max_chars_label = ttk.Label(config_frame, text="Max characters:", anchor='w')
        max_chars_label.pack(side=tk.LEFT, padx=(0, 5))

        max_chars_entry = ttk.Entry(config_frame, textvariable=self.max_chars_var, width=10)
        max_chars_entry.pack(side=tk.LEFT, ipady=2)

        generate_button = ttk.Button(self.master, text="Generate Summary", command=self.generate_summary_action)
        generate_button.pack(pady=10)

        output_frame = ttk.Frame(self.master, padding="10")
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)

        ttk.Label(output_frame, text="Output:", anchor='w').pack(fill='x', pady=(0, 2))

        self.output_text = tk.Text(output_frame, height=10, wrap='word')
        self.output_text.pack(fill='both', expand=True, ipady=5)

    def update_input_mode(self):
        mode = self.mode_var.get()
        # switch visible frames inside inputs_container so layout position is stable
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

        try:
            max_length = int(max_len_str)
            if max_length <= 0:
                messagebox.showerror("Błąd", "Maksymalna liczba znaków musi być dodatnią liczbą całkowitą.")
                return
        except ValueError:
            messagebox.showerror("Błąd", "Maksymalna liczba znaków musi być liczbą całkowitą.")
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
                # ujednolicenie: jeśli zwrócono krotkę/listę -> złącz elementy tekstowe
                if isinstance(scraped, (list, tuple)):
                    text = " ".join([s for s in scraped if s])
                else:
                    text = scraped or ""

            summary = get_summary(text, max_length)

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