import re
from xml.etree import ElementTree


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
            if element.tag != 'category':
                article[element.tag] = clean_text(element.text)
        articles.append(article.copy())
        article.clear()

    return articles


if __name__ == '__main__':
    # load from RSS feed
    data = import_data_from_file("../data/apnews.xml")

    print("Complete.")
