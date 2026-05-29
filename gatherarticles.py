"	https://api.elsevier.com/content/article/doi/[DOI]?view=FULL&httpAccept=text/plain&APIKey=f0acadd0199b030e18f6f4aff08e2263"


import logging
import random

import httpx
import time
from lxml import etree
from datetime import datetime
from lxml import etree

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

def request(url,id):
    timeout = httpx.Timeout(20.0, connect=60.0)
    client = httpx.Client(timeout=timeout)
    try:
        get = client.get(url)
        try:
            if get.status_code != None:
                return get
            else:
                request(url, id)
        except:
            request(url, id)

    except:
        logger.info(f"failed at collection the following article: {id}")
        request(url)


def scopus_paper_get(paper_doi,id=0):
    url=str(f"https://api.elsevier.com/content/article/doi/{paper_doi}?APIKey=ffa04d6dba0cd7d9cdf52c01ac352383&view=FULL")
    url = url.replace('"',"")
    print(url)
    response = request(url,id)
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

NS = {
    'ce': 'http://www.elsevier.com/xml/ja/ce',
    'mml': 'http://www.w3.org/1998/Math/MathML'
}

import re

def mathml_to_text(elem):
    # flatten all text in document order
    text = "".join(elem.itertext())

    # collapse XML whitespace/newlines
    text = re.sub(r"\s+", " ", text)

    # nicer operator spacing
    text = re.sub(r"\s*=\s*", " = ", text)
    text = re.sub(r"\s*/\s*", " / ", text)
    text = re.sub(r"\s*\+\s*", " + ", text)
    text = re.sub(r"\s*-\s*", " - ", text)

    return text.strip()


def node_to_text(node):

    parts = []

    if node.text:
        parts.append(node.text)

    for child in node:

        tag = etree.QName(child).localname

        # ----------------------------------------
        # DISPLAYED FORMULAS
        # ----------------------------------------

        if tag == "display":

            formula = child.xpath(".//mml:math", namespaces=NS)

            if formula:

                formula_text = mathml_to_text(formula[0])

                parts.append(f"\nFORMULA: {formula_text}\n")

        # ----------------------------------------
        # INLINE SUBSCRIPT
        # ----------------------------------------

        elif tag == "inf":

            sub = "".join(child.itertext()).strip()

            parts.append(f"_{sub}")

        # ----------------------------------------
        # INLINE SUPERSCRIPT
        # ----------------------------------------

        elif tag == "sup":

            sup = "".join(child.itertext()).strip()

            parts.append(f"^{sup}")

        # ----------------------------------------
        # HORIZONTAL SPACING
        # ----------------------------------------

        elif tag == "hsp":

            parts.append(" ")

        # ----------------------------------------
        # DEFAULT RECURSION
        # ----------------------------------------

        else:

            parts.append(node_to_text(child))

        # preserve trailing text
        if child.tail:
            parts.append(child.tail)

    # FINAL CLEANUP
    text = "".join(parts)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

def xml_conversion(id):


    xml_file = "reactorxml/"+id+".xml"

    tree = etree.parse(xml_file)
    if len(tree.xpath("//*[local-name()='body']"))<1:
        logger.info("article ignored: wrong format")
        return
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
            text = node_to_text(p)
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
            cells = [
                node_to_text(c)
                for c in row.xpath(".//*[local-name()='entry']")
            ]
            if cells:
                out.append(" | ".join(c.strip() for c in cells))

    with open("reactortxt/"+id+".txt", "w", encoding="utf-8") as f:
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
        time.sleep(3)

def requestreactors():
    with open("data/reactors.csv", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f,delimiter=";"))

    # Separate header and data
    header = reader[0]
    rows = reader[1:]

    # Pick 10 random rows
    random_rows = random.sample(rows, 100)

    # Print them
    print(header)
    count = 0
    for row in random_rows:
        doi = row[3].replace("http://dx.doi.org/","")
        text = scopus_paper_get(doi)
        if text != "":
            id = doi.replace("/",'_')
            with open("reactorxml/"+id+".xml", 'w') as f:
                f.write(text)
            xml_conversion(id)
            count+=1
            if count >=50: return
            print(count)
        else:
            print("empty article at: "+doi)
        time.sleep(3)

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs/logs{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])

requestreactors()





