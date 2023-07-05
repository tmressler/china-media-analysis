import os
import re
from xml.etree import ElementTree

import pandas
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from tqdm import tqdm


def clean_text(text: str) -> str:
    expression = r'<\/?a.*?>|<figure>.*?<\/figure>|<\/?p>|<div.*?>.*?<\/div>|<\/?h\d.*?>|<\/?strong>'
    return re.sub('\s+', ' ', re.sub(expression, ' ', text).strip())


def import_data_from_file(xml_file: str) -> list[dict[str: str]]:
    tree = ElementTree.parse(xml_file)
    root = tree.getroot()
    articles = []
    article = {}
    for item in root.findall('./channel/item'):
        for element in item:
            # if element.tag
            if element.tag == '{http://purl.org/rss/1.0/modules/content/}encoded':
                article['description'] = clean_text(element.text)
            elif element.tag in ['guid', 'title', 'pubDate']:
                article[element.tag] = clean_text(element.text)
        articles.append(article.copy())
        article.clear()

    return articles


def download_source_rss_feed(source: str, url: str, data_directory: str = 'data', force_download: bool = False) -> None:
    if os.path.exists(os.path.join(data_directory, source)) and not force_download:
        return

    try:
        session = HTMLSession()
        response = session.get(url)
    except requests.exceptions.RequestException as e:
        print(e)
        raise NotImplementedError

    data = pandas.DataFrame(columns=['title', 'pubDate', 'guid', 'description'])

    items = response.html.find("item", first=False)

    for item in items:
        title = item.find('title', first=True).text
        pubDate = item.find('pubDate', first=True).text
        guid = item.find('guid', first=True).text
        description = item.find('description', first=True).text

        data = data.append({'title': title, 'pubData': pubDate, 'guid': guid, 'description': description},
                           ignore_index=True)

    data.to_csv(os.path.join(data_directory, source))

    return


def analyze_source(source: str) -> dict:
    raise NotImplementedError


def parse_page(url: str) -> str:
    # get html from url and parse
    html_doc = requests.get(url).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    content = soup.find('div', class_='article__content')
    if not content:
        content = soup.find('div', class_='Article__content')
    if content:
        return content.text
    else:
        return ''


def manual_import(*args):
    links = [
        "https://www.cnn.com/2023/04/15/asia/taiwan-china-invasion-defense-us-weapons-intl-hnk-dst/index.html",
        "https://www.cnn.com/2023/03/24/asia/taiwan-diplomatic-allies-support-analysis-intl-hnk-dst/index.html",
        "https://www.cnn.com/2023/04/13/china/china-sea-level-record-high-2022-climate-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/14/china/xi-jinping-lula-china-brazil-world-leaders-visit-beijing-intl-hnk-mic/index.html",
        "https://www.cnn.com/2023/04/11/politics/taiwan-foreign-minister-interview/index.html",
        "https://www.cnn.com/2023/04/16/china/china-defense-minister-visit-russia-vladimir-putin-li-shangfu-intl-hnk/index.html",
        "https://www.cnn.com/travel/article/china-lesser-known-destinations/index.html",
        "https://www.cnn.com/travel/article/china-beautiful-great-wall-sections-cmd/index.html",
        "https://www.cnn.com/2023/03/28/economy/china-rescue-lending-belt-and-road-study-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/10/asia/china-taiwan-military-drills-aircraft-carrier-strike-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/14/china/us-citizen-death-sentence-upheld-china-intl-hnk/index.html",
        "https://www.cnn.com/2023/03/07/china/china-two-sessions-new-foreign-minister-us-rebuke-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/06/asia/china-taiwan-reaction-tsai-ing-wen-mccarthy-meeting-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/11/americas/lula-brazil-china-visit-intl-latam/index.html",
        "https://www.cnn.com/2023/03/24/asia/us-navy-operation-paracels-china-intl-hnk-ml/index.html",
        "https://www.cnn.com/2023/04/07/china/china-taiwan-military-exercises-hnk-intl-ml/index.html",
        "https://www.cnn.com/travel/article/china-new-outdoor-attractions-2023/index.html",
        "https://www.cnn.com/2023/04/11/china/china-pentagon-documents-leak-ukraine-intl-hnk-mic/index.html",
        "https://www.cnn.com/2023/03/31/middleeast/saudi-china-get-closer-mime-intl/index.html",
        "https://www.cnn.com/2023/04/06/health/who-china-share-covid/index.html",
        "https://www.cnn.com/2023/04/11/asia/china-sandstorm-hits-beijing-intl-hnk/index.html",
        "https://www.cnn.com/2023/03/08/economy/china-two-sessions-state-council-shakeup-intl-hnk/index.html",
        "https://www.cnn.com/2023/03/15/world/us-saudi-china-relations-intl/index.html",
        "https://www.cnn.com/2023/04/08/asia/chicken-scarer-jail-china-intl-hnk/index.html",
        "https://www.cnn.com/2023/03/09/china/china-xi-jinping-president-third-term-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/09/asia/china-taiwan-simulated-attacks-military-drills-day-two-intl-hnk-mil/index.html",
        "https://www.cnn.com/2023/03/07/economy/china-two-sessions-xi-jinping-speech-us-challenges-intl-hnk/index.html",
        "https://www.cnn.com/2023/03/06/economy/china-two-sessions-lowest-gdp-target-analysis-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/02/tech/china-pinduoduo-malware-cybersecurity-analysis-intl-hnk/index.html",
        "https://www.cnn.com/2023/04/03/politics/chinese-spy-balloon/index.html",
    ]

    texts = []
    for link in links:
        texts.append({"url": link, "content": clean_text(parse_page(link))})

    return texts


def import_data(url: str) -> list[dict[str, str]]:
    # get html from url and parse
    html_doc = requests.get(url).text
    soup = BeautifulSoup(html_doc, 'html.parser')

    # check each href in html for pdfs
    urls = []
    contents = []
    for link in tqdm(soup.find_all('a')):
        href = link.get('href')
        if href and (href.lower().startswith('/world/') or href.lower().startswith('/politics/')):
            href = "https://www.foxnews.com" + href
            content = clean_text(parse_page(href))
            if 'china' in content.lower() and content not in contents:
                urls.append(href)
                contents.append(content)

    return [{"url": href, "content": content} for href, content in zip(urls, contents)]


def main():
    # load from manual links
    manual_import()


if __name__ == '__main__':
    main()
