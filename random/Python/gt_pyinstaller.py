import tkinter as tk
from googletrans import Translator

def translate(text:str, translate_to:str='jp'):
    translator = Translator()
    translation = translator.translate(text, dest=translate_to)
    return translation.text

class texts:
    def __init__(self, text:str):
        self.text = text        

app = tk.Tk()
app.title("Google Translate Test")

to_translate = tk.Entry(app)
to_translate.grid(row=0, column=0, columnspan=5)
translation_label = tk.Label(app, text="")
translate_button = tk.Button(app, text="Translate", command=lambda:translation_label.config(text=translate(to_translate.get())))
translate_button.grid(row=0, column=6)
translation_label.grid(row=1, column=2)

app.mainloop()