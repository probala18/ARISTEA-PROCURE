import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

# --------------------------------------------------
# BIS PAGE URL
# --------------------------------------------------

URL = "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/get_is_list_by_category_id/1"

# --------------------------------------------------
# DOWNLOAD PAGE
# --------------------------------------------------

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Downloading BIS page...")

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()

print("Page downloaded successfully!")

# --------------------------------------------------
# PARSE HTML
# --------------------------------------------------

soup = BeautifulSoup(response.text, "html.parser")

# --------------------------------------------------
# FIND TABLE
# --------------------------------------------------

table = soup.find("table")

if table is None:
    print("ERROR: No table found!")
    exit()

print("BIS table found!")

# --------------------------------------------------
# SCRAPE ROWS
# --------------------------------------------------

data = []

for row in table.find_all("tr"):

    cells = row.find_all(["td", "th"])

    if not cells:
        continue

    values = [
        cell.get_text(" ", strip=True)
        for cell in cells
    ]

    # Print what Python sees
    print(values)

    # Skip header
    if values[0].lower() == "sr no.":
        continue

    # We need at least 3 columns
    if len(values) < 3:
        continue

    sr_no = values[0]
    is_number = values[1]
    product = values[2]

    notification = ""

    if len(values) >= 4:
        notification = values[3]

    # --------------------------------------------------
    # GET NOTIFICATION LINKS
    # --------------------------------------------------

    notification_links = []

    if len(cells) >= 4:

        for link in cells[3].find_all("a", href=True):

            link_text = link.get_text(" ", strip=True)

            link_url = urljoin(
                URL,
                link["href"]
            )

            notification_links.append({
                "text": link_text,
                "url": link_url
            })

    # --------------------------------------------------
    # SAVE ROW
    # --------------------------------------------------

    data.append({
        "sr_no": sr_no,
        "is_number": is_number,
        "product": product,
        "notification": notification,
        "notification_links": notification_links
    })


# --------------------------------------------------
# CREATE DATAFRAME
# --------------------------------------------------

df = pd.DataFrame(data)

print()
print("--------------------------------")
print("SCRAPING COMPLETE")
print("--------------------------------")

print("Total rows:", len(df))

print()
print(df.head(10).to_string(index=False))


# --------------------------------------------------
# SAVE CSV
# --------------------------------------------------

df.to_csv(
    "bis_standards.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("CSV saved as:")
print("bis_standards.csv")


# --------------------------------------------------
# SAVE JSON
# --------------------------------------------------

df.to_json(
    "bis_standards.json",
    orient="records",
    indent=4,
    force_ascii=False
)

print()
print("JSON saved as:")
print("bis_standards.json")