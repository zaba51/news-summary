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

        self.url_var = tk.StringVar()
        self.max_chars_var = tk.StringVar(value="500")

        self.create_widgets()

    def create_widgets(self):
        url_frame = ttk.Frame(self.master, padding="10")
        url_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(url_frame, text="Paste your url here:", anchor='w').pack(fill='x', pady=(0, 2))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        url_entry.pack(fill='x', ipady=5)

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

    def generate_summary_action(self):
        url = self.url_var.get().strip()
        max_len_str = self.max_chars_var.get().strip()

        if not url:
            messagebox.showerror("Błąd", "Proszę podać URL artykułu.")
            return

        try:
            max_length = int(max_len_str)
            if max_length <= 0:
                messagebox.showerror("Błąd", "Maksymalna liczba znaków musi być dodatnią liczbą całkowitą.")
                return
        except ValueError:
            messagebox.showerror("Błąd", "Maksymalna liczba znaków musi być liczbą całkowitą.")
            return

        self.output_text.delete(1.0, tk.END)  # Czyść poprzedni wynik
        self.output_text.insert(tk.END, "Trwa generowanie podsumowania... Proszę czekać.")
        self.master.update()

        try:
            text = scrape_text_from_url(url)
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