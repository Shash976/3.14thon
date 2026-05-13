import pathlib
import googletrans
from googletrans import Translator, LANGUAGES
import os
import subprocess
import io
from multiprocessing import Pool

translator = Translator()
locale_dir = pathlib.Path('locales')
full_path = r"C:\Users\shash\Desktop\Code\VSC\test\Python\language\t5\locales"
codes = list(LANGUAGES.keys())

make_pot_command = ["xgettext", "-d", "base", "-o", r"C:\Users\shash\Desktop\Code\VSC\test\Python\language\t5\locales\base.pot", r"C:\Users\shash\Desktop\Code\VSC\test\Python\language\t5\main.py"]
run = subprocess.run(make_pot_command, capture_output=True) 
print(run.stderr)
pot_template = open(r"C:\Users\shash\Desktop\Code\VSC\test\Python\language\t5\locales\base.pot", "r")
placeholder_text = pot_template.read()
placeholder_text = placeholder_text.replace("CHARSET", "utf-8")

import re
def get_final_text(text:str, language:str="en"):
    enter_lang = text.index("Language: ")+len("Language: ")-1
    text = text[:enter_lang] + language + text[enter_lang:]
    matches = re.finditer('msgid "(.*)"', text)
    additional = 0
    for match in matches:
        target = text[match.start()+7+additional:match.end()-1+additional]
        if len(target) > 0:
            var = re.findall("{(.*)}", target)
            target = re.sub("{.*}", r"  ====  ",target)    
            translation = translator.translate(target, dest=language).text
            var = var if len(var) < 1 else " {" + var[0] + "} "
            target = re.sub(r"====", var, translation ) if type(var) is str else translation
            msgstr = re.search('msgstr "(.*)"', text[match.end():])

            text = text[:msgstr.start()+match.end()+8] + target + text[msgstr.end()-1+match.end():]
            additional += len(target)
    return text

def process_language(language_code):
    language = googletrans.LANGUAGES[language_code]
    base = os.path.join(full_path, language_code, "LC_MESSAGES")
    os.makedirs(base)
    base = os.path.join(base, "base.po")
    text_to_write = get_final_text(text=placeholder_text, language=language_code)
    print("Writing for lang", language_code, " -> ", language)
    make_mo_command = ["msgfmt", "-o", f"locales/{language_code}/LC_MESSAGES/base.mo", f"locales/{language_code}/LC_MESSAGES/base.po"]
    try:
        with io.open(base, "w+", encoding='utf-8') as file:
            file.write(text_to_write)
        run = subprocess.run(make_mo_command, capture_output=True)
    except Exception as err:
        print("this is the error, ",err)
        print(text_to_write[650:700])

if __name__ == "__main__":
    with Pool(5) as pool:
        result = pool.map(process_language, codes)
    print("Program Finished")