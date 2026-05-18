"	https://api.elsevier.com/content/article/doi/[DOI]?view=FULL&httpAccept=text/plain&APIKey=f0acadd0199b030e18f6f4aff08e2263"


import logging
import httpx
import time
from lxml import etree
from datetime import datetime

import csv

logger = logging.getLogger(__name__)

def extract_dois(csv_file):
    DOI = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            param = row[0].split(";")
            doi = param[2].replace("http://dx.doi.org/", "")
            id = param[1]
            DOI.append([id,doi])
    return DOI


def scopus_paper_get(paper_doi,id):
    apikey="f0acadd0199b030e18f6f4aff08e2263"
    doi = paper_doi
    timeout = httpx.Timeout(20.0, connect=60.0)
    client = httpx.Client(timeout=timeout)
    url=str(f"https://api.elsevier.com/content/article/doi/{doi}?APIKey=5e6651f887493707ac5b67174ae5b51a&view=FULL")
    print(str(url))
    response=client.get(url)
    if response.status_code != 200:
        logger.info(f"{response.status_code} - id:{id}")
        return ""
    print(response)
    root = etree.fromstring(response.content)

    # Namespace for Elsevier's XML
    ns = {
        'ce': 'http://www.elsevier.com/xml/ja/ce',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xocs': 'http://www.elsevier.com/xml/xocs/dtd',
        'dcterms': 'http://purl.org/dc/terms/',
        'prism': 'http://prismstandard.org/namespaces/basic/2.0/'
    }

    # Extract abstract and body text (adjust XPath as needed)
    abstract = root.xpath('//dc:description', namespaces=ns)
    body = root.xpath('//ce:para', namespaces=ns)

    # Combine all text
    #clean_text = "\n".join(abstract + body)
    return response.text

def xml_conversion(id):
    from lxml import etree

    xml_file = "articlexml/"+id+".xml"

    tree = etree.parse(xml_file)

    body = tree.xpath("//*[local-name()='body']")[0]
    head = tree.xpath("//*[local-name()='head']")[0]
    out = []

    title = head.xpath("./*[local-name()='title']//text()")
    out.append("TITLE: " + "".join(title).strip())
    # sections
    for section in body.xpath(".//*[local-name()='section']"):

        # title
        titles = section.xpath("./*[local-name()='section-title']//text()")
        numbering = section.xpath("./*[local-name()='label']//text()")
        if titles:
            out.append("\n" + "".join(numbering).strip() + " " + " ".join(titles).strip())
        # paragraphs
        paras = section.xpath("./*[local-name()='para']")
        for p in paras:
            text = " ".join(p.xpath(".//text()"))
            out.append(text.strip())

    # figures
    for fig in body.xpath(".//*[local-name()='figure']"):

        caption = fig.xpath(".//*[local-name()='caption']//text()")
        if caption:
            out.append("\n[FIGURE]")
            out.append(" ".join(caption).strip())

    # tables
    for table in body.xpath(".//*[local-name()='table']"):

        caption = table.xpath(".//*[local-name()='caption']//text()")
        if caption:
            out.append("\n[TABLE]")
            out.append("Caption: " + " ".join(caption).strip())

        rows = table.xpath(".//*[local-name()='row']")
        for row in rows:
            cells = row.xpath(".//*[local-name()='entry']//text()")
            if cells:
                out.append(" | ".join(c.strip() for c in cells))

    with open("articletxt/"+id+".txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(out))


def requestarticles():
    links = extract_dois("data/articlelist.csv")
    count = 0
    for article in links:
        id = str(article[0])
        print("articleid: "+id)
        link = article[1]
        text = scopus_paper_get(link,id)
        if text != "":
            with open("articlexml/"+id+".xml", 'w') as f:
                f.write(text)
            xml_conversion(id)
            count+=1
            print(count)
        else:
            print("empty article at: "+link)
        time.sleep(5)

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs/logs{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])


requestarticles()





