from collections import Counter, ChainMap

import pandas
import seaborn
import spacy
from matplotlib import pyplot
from tqdm import tqdm

from src.ap_news_data import import_data_from_file as import_ap_news_data
from src.cnn_news_data import manual_import as import_cnn_news_data
from src.committee_data import import_data as import_committee_data
from src.fox_news_data import manual_import as import_fox_news_data
from src.reuters_news_data import manual_import as import_reuters_news_data

# entities and what entity class they belong to
classes = {
    "Political Figures":
        {
            'Xi Jinping': ['xi jinping'],
            'Mao Ning': ['mao ning'],
            'Qin Gang': ['qin gang']
        },
    "Political Entities":
        {
            "CCP": ["the chinese communist party's", 'the chinese communist party', 'chinese communist party',
                    'communist party', 'the ccp', 'ccp'],
            "Central Committee": ['the central committee', 'central committee'],
            "Chinese Embassy": ['the chinese embassy'],
            "PLA": ['pla', "people's liberation army", "the people's liberation army"]
        },
    "Geopolitical Entities":
        {
            "China": ['china', "the people's republic of china"],
            "Beijing": ['beijing'],
            "Zhongnanhai": ['zhongnanhai']
        }
}


def main():
    # maps for each source to load their documents
    source_data = [
        {
            "Organization": "Committee",
            "Loader": import_committee_data,
            "Link": "https://selectcommitteeontheccp.house.gov/committee-activity/hearings/chinese-communist-partys-threat-america",
            "UrlLabel": "url",
            "TextLabel": "content"
        },
        {
            "Organization": "AP News",
            "Loader": import_ap_news_data,
            "Link": "data/apnews.xml",
            "UrlLabel": "link",
            "PublishedLabel": "pubDate",
            "TextLabel": "description"
        },
        {
            "Organization": "Fox News",
            "Loader": import_fox_news_data,
            "UrlLabel": "url",
            "PublishedLabel": "date",
            "TextLabel": "content"
        },
        {
            "Organization": "CNN",
            "Loader": import_cnn_news_data,
            "UrlLabel": "url",
            "TextLabel": "content"
        },
        {
            "Organization": "Reuters",
            "Loader": import_reuters_news_data,
            "UrlLabel": "url",
            "TextLabel": "content"
        }
    ]

    # find distribution of entities for each source
    nlp = spacy.load("en_core_web_trf")
    source_entities = []
    for source in source_data:
        entities = []
        documents = []
        for d, document in enumerate(tqdm(source['Loader'](source['Link'] if 'Link' in source else None),
                                          desc=f'Processing {source["Organization"]}')):
            documents.append({'url': document[source['UrlLabel']],
                              'date': document[source['PublishedLabel']] if 'PublishedLabel' in source else None,
                              'text': document[source['TextLabel']]})
            parsed_document = nlp(document[source['TextLabel']])
            entities += [str(entity).strip().replace('\n', '') for entity in parsed_document.ents if
                         entity.label_ in ['PERSON', 'GPE', 'ORG']]
        source_entities.append(
            {"Organization": source["Organization"], "Counts": Counter(entities.copy()), "Documents Count": d})
        pandas.DataFrame(documents).to_json(f"data/{source['Organization'].lower().replace(' ', '_')}.jsonl.gz",
                                            orient='records', lines=True)

    # filter entities and organize into figure data
    data = {}
    for source in source_entities:
        for token, count in source["Counts"].items():
            for class_name, class_members in classes.items():
                for member, pseudonyms in class_members.items():
                    if token.lower() in pseudonyms:
                        if (member, source["Organization"]) not in data:
                            data.update({(member, source["Organization"]): count})
                        else:
                            data.update(
                                {(member, source["Organization"]): data[(member, source["Organization"])] + count})

    data = pandas.DataFrame([(key[0], key[1], value) for key, value in data.items()],
                            columns=['Class', 'Organization', 'Raw Count'])
    data["Document Counts"] = data["Organization"].apply(
        lambda x: {source["Organization"]: source["Documents Count"] for source in source_entities}[x])
    data["Mentions per Document"] = data["Raw Count"] / data["Document Counts"]

    data_counts = data[["Class", "Organization", "Raw Count"]].set_index(['Organization', 'Class'])[
        "Raw Count"].unstack()
    data_class_counts = data_counts.groupby(data_counts.columns.map(
        dict(ChainMap(*[{item: class_ for item in list(classes[class_].keys())} for class_ in classes]))), axis=1).sum()

    # create a figure illustrating entity mentions across different organizations
    fig, axes = pyplot.subplots(2, 2, dpi=144, figsize=(18, 18))
    seaborn.barplot(data, x="Class", y="Raw Count", hue="Organization", ax=axes[0][0])
    seaborn.barplot(data, x="Class", y="Mentions per Document", hue="Organization", ax=axes[0][1])
    data_counts.div(data_counts.sum(axis=1), axis=0).plot(kind='bar', stacked=True, ax=axes[1][0])
    data_class_counts.div(data_class_counts.sum(axis=1), axis=0).plot(kind='bar', stacked=True, ax=axes[1][1])
    axes[0][0].set_title("Raw Entity Mentions by Organization")
    axes[0][1].set_title("Mentions per Document by Organization")
    axes[1][0].set_title("Proportion of Entity Mentions by Organization")
    axes[1][0].set_ylabel("Percent")
    axes[1][1].set_title("Proportion of Entity Mentions Classes by Organization")
    axes[1][1].set_ylabel("Percent")
    pyplot.tight_layout()
    fig.suptitle("References to Chinese Entities by Organizations")
    pyplot.show()

    return


if __name__ == '__main__':
    main()
