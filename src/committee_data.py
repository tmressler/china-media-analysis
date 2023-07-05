import re
from io import BytesIO

import requests
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup


def parse_pdf(pdf_url: str) -> str:
    pdf_file = requests.get(pdf_url)
    bytes_stream = BytesIO(pdf_file.content)
    reader = PdfReader(bytes_stream)
    pdf_text = ''
    for page in reader.pages:
        pdf_text += re.sub(r'\s+', ' ', re.sub(r'\n|1 http.*', ' ', page.extractText())).strip()

    return pdf_text


def clean_text(text: str) -> str:
    expression = r'<\/?a.*?>|<figure>.*?<\/figure>|<\/?p>|<div.*?>.*?<\/div>|<\/?h\d.*?>'
    return re.sub('\s+', ' ', re.sub(expression, ' ', text).strip())


def import_data(url: str) -> list[dict[str, str]]:
    # get html from url and parse
    html_doc = requests.get(url).text
    soup = BeautifulSoup(html_doc, 'html.parser')

    # check each href in html for pdfs
    pdf_data = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.lower().endswith('.pdf'):
            pdf_data.append({"url": href, "content": clean_text(parse_pdf(href))})

    return pdf_data


if __name__ == '__main__':
    data = import_data(
        "https://selectcommitteeontheccp.house.gov/committee-activity/hearings/chinese-communist-partys-threat-america")

    print("Complete.")
