import tkinter as tk
from tkinter import ttk
from googletrans import Translator, LANGUAGES

class OriginalText:
    def __init__(self):
        self.text_text_to_translate = "To Translate: "
        self.text_text_translate = "Translate"
        self.text_text_translation = "This is the translation: "
        self.text_text_language_select = "Select Language: "
    def translate(self, language):
        translator = Translator()
        self.text_text_to_translate = translator.translate(self.text_text_to_translate, dest=language).text
        self.text_text_translate = translator.translate(self.text_text_translate, dest=language).text
        self.text_text_translation = translator.translate(self.text_text_translation, dest=language).text
        self.text_text_language_select = translator.translate(self.text_text_language_select, dest=language).text

app = tk.Tk()
app.title("Google Translate Test")

def reset_app():
    for widget in app.winfo_children():
        widget.destroy()
    create_widgets()

texts = OriginalText()

def create_widgets():
    to_translate = tk.Label(app, text=texts.text_text_to_translate)
    to_translate.pack()
    translate = tk.Label(app, text = texts.text_text_translate)
    translate.pack()
    translation = tk.Label(app, text = texts.text_text_translation)
    translation.pack()
    language_select = tk.Label(app, text=texts.text_text_language_select)
    language_select.pack()

    language_dropdown = ttk.Combobox(app, values=list(LANGUAGES.keys()))
    language_dropdown.set('en')
    def selected_language(event):
        language = language_dropdown.get()
        texts.translate(language)
        reset_app()

    language_dropdown.bind("<<ComboboxSelected>>", selected_language)
    language_dropdown.pack()

create_widgets()

app.mainloop()