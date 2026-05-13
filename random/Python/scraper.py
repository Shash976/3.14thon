import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. URL of the SURF projects page
URL = "https://engineering.purdue.edu/Engr/Research/EURO/SURF/Research/Y2026"

# 2. Download page
response = requests.get(URL)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

projects_data = []

# 3. Loop through each project
projects = soup.find_all("div", class_="research-project")

for project in projects:
    project_dict = {}

    # --- Project Title ---
    title_tag = project.find("h3", class_="research-title")
    project_dict["Title"] = title_tag.get_text(strip=True) if title_tag else ""

    # --- All rows (label/value pairs) ---
    rows = project.find_all("div", class_="row")
    for row in rows:
        label_div = row.find("div", class_="label")
        value_div = row.find("div", class_="value")

        if label_div and value_div:
            label = label_div.get_text(strip=True).replace(":", "")
            value = " ".join(value_div.stripped_strings)
            project_dict[label] = value

    more_info_url = ""
    p_tags = project.find_all("p")

    for p in p_tags:
        a_tag = p.find("a", href=True)
        if a_tag and "more" in p.get_text(strip=True).lower():
            more_info_url = a_tag["href"]
            break

    project_dict["More Info URL"] = more_info_url

    projects_data.append(project_dict)


# 4. Convert to DataFrame
df = pd.DataFrame(projects_data)

# 5. Save to CSV
df.to_csv("purdue_surf_projects.csv", index=False)

print(f"Saved {len(df)} projects to purdue_surf_projects.csv")
