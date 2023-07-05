import os
import re
from xml.etree import ElementTree

import pandas
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from tqdm import tqdm


def clean_text(text: str) -> str:
    expression = r'^.*\(Reuters\)\s-\s'
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


def parse_page(url: str) -> tuple[str, str]:
    # get html from url and parse
    html_doc = requests.get(url).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    if soup.find('date'):
        date = soup.find('date').text
    text = soup.find('div', class_='article-body__content__17Yit').text
    return date, text


#
def manual_import(*args):
    links = [
        "https://www.reuters.com/world/asia-pacific/g7-discuss-common-concerted-approach-china-us-official-says-2023-04-16/",
        "https://www.reuters.com/world/china-hopes-germany-supports-peaceful-taiwan-reunification-foreign-ministry-2023-04-15/",
        "https://www.reuters.com/world/china-takes-swipe-western-friend-shoring-efforts-2023-04-14/",
        "https://www.reuters.com/world/us-warship-sails-through-taiwan-strait-following-china-war-games-2023-04-17/",
        "https://www.reuters.com/world/asia-pacific/china-launches-weather-satellite-flights-avoid-no-fly-zone-north-taiwan-2023-04-16/",
        "https://www.reuters.com/world/china/china-march-new-home-prices-rise-fastest-pace-since-june-2021-2023-04-15/",
        "https://www.reuters.com/world/putin-meets-chinese-defence-minister-hails-military-cooperation-2023-04-16/",
        "https://www.reuters.com/markets/asia/chinas-largest-trade-fair-exporters-worry-about-world-economy-2023-04-16/",
        "https://www.reuters.com/world/us-says-it-is-monitoring-chinas-drills-around-taiwan-closely-2023-04-08/",
        "https://www.reuters.com/world/china/china-march-new-home-prices-rise-fastest-pace-since-june-2021-2023-04-15/",
        "https://www.reuters.com/world/china-brazil-reset-ties-with-tech-environment-accords-agree-ukraine-2023-04-14/",
        "https://www.reuters.com/world/china/china-out-uns-wildlife-survey-pandemic-controls-source-2023-04-13/",
        "https://www.reuters.com/world/asia-pacific/japan-following-chinas-taiwan-drills-with-great-interest-2023-04-10/",
        "https://www.reuters.com/breakingviews/china-reluctantly-keeps-sanctions-powder-dry-2023-04-12/",
        "https://www.reuters.com/world/china-sanctions-senior-us-lawmaker-visiting-taiwan-2023-04-13/",
        "https://www.reuters.com/world/asia-pacific/china-denies-imposing-no-fly-zone-north-taiwan-2023-04-14/",
        "https://www.reuters.com/world/asia-pacific/taiwan-president-says-china-military-exercises-not-responsible-2023-04-10/",
        "https://www.reuters.com/world/high-hopes-china-eu-leaders-prepare-xi-talks-2023-04-06/",
        "https://www.reuters.com/markets/china-spent-240-bln-bailing-out-belt-road-countries-study-2023-03-27/",
        "https://www.reuters.com/business/energy/china-doubles-down-coal-ahead-potential-summer-blackouts-2023-04-12/",
        "https://www.reuters.com/world/asia-pacific/taiwan-determined-safeguard-freedom-democracy-president-tsai-says-2023-04-12/",
        "https://www.reuters.com/world/europe/germany-foreign-minister-embarks-post-macron-damage-control-china-trip-2023-04-12/",
        "https://www.reuters.com/world/us-seeks-allies-backing-possible-china-sanctions-over-ukraine-war-sources-2023-03-01/",
        "https://www.reuters.com/world/europe/macrons-aim-eu-unity-china-undone-by-trip-fallout-2023-04-11/",
        "https://www.reuters.com/world/asia-pacific/we-are-all-chinese-former-taiwan-president-says-while-visiting-china-2023-03-28/",
        "https://www.reuters.com/world/china/china-says-if-us-does-not-change-path-towards-it-there-will-surely-be-conflict-2023-03-07/",
        "https://www.reuters.com/world/china-announces-drills-around-taiwan-after-us-speaker-meeting-2023-04-08/",
        "https://www.reuters.com/world/china/china-raise-retirement-age-deal-with-aging-population-media-2023-03-14/",
        "https://www.reuters.com/world/asia-pacific/china-close-airspace-north-taiwan-april-16-18-sources-2023-04-12/",
        "https://www.reuters.com/world/eu-cannot-trust-china-unless-it-seeks-peace-ukraine-borrell-2023-04-14/",
        "https://www.reuters.com/technology/brazil-paves-way-semiconductor-cooperation-with-china-2023-04-14/"
    ]

    texts = []
    for link in links:
        date, content = parse_page(link)
        texts.append({"url": link, "date": date, "content": clean_text(content)})

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
            date, content = clean_text(parse_page(href))
            if 'china' in content.lower() and content not in contents:
                urls.append(href)
                contents.append(content)

    return [{"url": href, "content": content} for href, content in zip(urls, contents)]


def main():
    manual_import()


if __name__ == '__main__':
    main()
