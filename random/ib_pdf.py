import re
import os

expression = r"/IB\\(\w+)\\.*\\(19|20\d{2}) (\w+).*\\(\w+)_paper.*(1|2|3)_.*(HL|SL)?:*(?:(Spanish|French)).pdf/gmi"

strings = [
    r"C:\Users\shash\OneDrive - Nord Anglia Education\IB\Math\Past Papers\Mathematics_analysis_and_approaches_SL\2022 May Examination Session\Mathematics_analysis_and_approaches_paper_2__TZ1_SL.pdf",
    r"C:\Users\shash\OneDrive - Nord Anglia Education\IB\CS\Past Papers\2007 May Examination Session\Computer_science_paper_2_HL_French.pdf"
]

subjects = [os.path.join(os.getcwd(), subject) for subject in os.listdir()] 
past_paper_folders = []
for subject in subjects:
    folders = os.listdir(subject)
    for folder in folders:
        if "Past Papers" in folder:
            ppf_path = os.path.join(subject, folder)
            past_paper_folders.append(ppf_path)
            for compartments_under_ppf in os.listdir(ppf_path):
                pass