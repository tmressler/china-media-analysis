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


def parse_page(url: str) -> tuple[str, str]:
    # get html from url and parse
    html_doc = requests.get(url).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup.find('time').text, soup.find('div', class_='article-body').text


def manual_import(*args):
    links = [
        "https://www.foxnews.com/world/china-says-hopes-believes-germany-will-support-peaceful-reunification-taiwan",
        "https://www.foxnews.com/world/china-expands-wartime-military-draft-include-veterans-college-students",
        "https://www.foxnews.com/opinion/america-can-defeat-china-win-future-if-we-one-thing",
        "https://www.foxnews.com/world/china-warning-us-philippines-stage-largest-ever-drills",
        "https://www.foxnews.com/world/ai-threat-humanity-far-greater-china-masters-first-gordon-chang",
        "https://www.foxnews.com/opinion/us-needs-stop-china-here-are-best-ways-do-it",
        "https://www.foxnews.com/media/sean-hannity-chinas-dangerous-coalition-is-growing",
        "https://www.foxnews.com/opinion/china-plan-lead-world-what-ours",
        "https://www.foxnews.com/politics/house-china-chairman-warns-biden-not-moving-appropriate-sense-urgency-prevent-world-war-iii",
        "https://www.foxnews.com/world/china-sanctions-us-lawmaker-visit-taiwan-claiming-violated-one-china-principle",
        "https://www.foxnews.com/world/chinas-xi-host-brazils-lula-beijing-secure-economic-ties",
        "https://www.foxnews.com/media/chinese-almost-every-country-latin-america-rep-henry-cuellar",
        "https://www.foxnews.com/world/china-sanctions-us-lawmaker-visit-taiwan-claiming-violated-one-china-principle",
        "https://www.foxnews.com/politics/what-might-happen-next-chinese-invasion-taiwan-impact-united-states",
        "https://www.foxnews.com/world/china-flexes-muscles-latin-america-latest-security-challenge-us",
        "https://www.foxnews.com/world/conflict-china-last-resort-congress-will-authorize-troops-americans-support-it-mccaul",
        "https://www.foxnews.com/media/biden-weakness-led-brazil-egypt-uae-china-over-america-senator",
        "https://www.foxnews.com/world/china-wants-taiwan-historical-value-disrupt-global-power-dynamic-experts",
        "https://www.foxnews.com/politics/future-now-china-russia-revert-1989-world-challenge-us-west",
        "https://www.foxnews.com/politics/us-very-confident-can-protect-interests-south-china-sea-china-surrounds-taiwan",
        "https://www.foxnews.com/politics/heritage-foundation-declares-new-cold-war-with-china-more-capable-and-dangerous-than-soviet-union",
        "https://www.foxnews.com/world/china-says-drills-around-taiwan-are-serious-warning",
        "https://www.foxnews.com/world/china-conducts-second-day-military-drills-taiwan-simulates-strikes-island",
        "https://www.foxnews.com/world/xi-accuses-us-suppression-containment-china",
        "https://www.foxnews.com/world/china-holds-military-advantage-over-us-washington-prepares-conflict-taiwan-retired-general-says",
        "https://www.foxnews.com/politics/china-disturbing-path-eclipse-us-military-mid-century-milley-warns",
        "https://www.foxnews.com/world/china-not-sell-weapons-either-side-war-ukraine-according-foreign-minister",
        "https://www.foxnews.com/world/china-threatens-serious-consequences-us-warship-sails-contested-paracel-islands",
        "https://www.foxnews.com/world/china-xi-demands-rapid-military-upgrade-world-class-standards",
        "https://www.foxnews.com/politics/chinese-embassy-emails-house-republican-staff-expressing-grave-concern-with-covid-19-origins-hearing",
        "https://www.foxnews.com/world/china-denies-hidden-motives-brokering-talks-saudi-arabia-iran",
        "https://www.foxnews.com/world/china-sends-fighter-jets-toward-taiwan-tsai-us-meeting"
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
