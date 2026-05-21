import csv
import json

### Gathering the filters obtained from the manual filtering for the article list

def extract_dois(csv_file):
    DOI = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f,delimiter=";")
        for row in reader:
            doi = row[2]
            id = row[1]
            DOI.append([id,doi])
    return DOI


def get_article_id(doi):
    links = extract_dois("data/articlelist.csv")
    for i in range(1,len(links)):
        if str(doi) in str(links[i][1]):
            return links[i][0]
    return 0

def get_manual_review(csv_file, article_id):
    results = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=",")

        for row in reader:
            doi = str(row[5])
            id = get_article_id(doi)
            if id != 0 and str(id) == str(article_id):
                datapoint = [id, row[7]]
                if datapoint not in results:
                    results.append(datapoint)
    #print(results)
    return results

### Gather results from the LLM filtering on the article list


pretreatment_map = {
    1: "mechanical desintegration",
    2: "thermal",
    3: "ultrasonic",
    4: "pressure",
    5: "pulsed electric field",
    6: "alkaline",
    7: "acidic",
    8: "oxidizer",
    9: "solvent",
    10: "other",
    11: "enzyme",
    12: "fungi",
    13: "microbial consortium",
    14: "biological active substrate",
    15: "nanoparticles",
    16: "disinhibition",
    17: "chelating",
    18: "nutrient",
    58: "microaerobic"
}


def get_llm_review(json_file):
    results = []
    article_id = json_file.replace(".json","").replace("ptoutput/","")
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
        filters = data.get("filters")
        for item in filters:
            answer = str(item.get("answer")).lower()
            if answer == "true":
                qid = item.get("qid")
                pretreatment = pretreatment_map[qid]
                datapoint = [article_id, pretreatment]
                results.append(datapoint)
    return results

### Compare results from both sources

def compare(manual, llm):
    manual_filtered = [item for item in manual if item[1] != pretreatment_map[10]]
    llm_filtered = [item for item in llm if item[1] != pretreatment_map[10]]
    correct_predictions = 0
    false_predictions = 0
    missed_predictions = 0

    correct_items = []
    false_items = []
    missed_items = []

    for item in llm_filtered:
        if item in manual_filtered:
            correct_predictions += 1
            correct_items.append(item)
        else:
            false_predictions += 1
            false_items.append(item)

    for item in manual_filtered:
        if item not in llm_filtered:
            missed_predictions += 1
            missed_items.append(item)

    precision = 0
    recall = 0
    f1_score = 0

    if (correct_predictions + false_predictions) > 0:
        precision = (
                correct_predictions / (correct_predictions + false_predictions)
        )
    if (correct_predictions + missed_predictions) > 0:
        recall = (
                correct_predictions / (correct_predictions + missed_predictions)
        )
    if (precision + recall) > 0:
        f1_score = (
                2 * precision * recall / (precision + recall)
        )
    report = {
        "manual_review": manual_filtered,
        "llm_review": llm_filtered,
        "correct_predictions": correct_predictions,
        "false_predictions": false_predictions,
        "missed_predictions": missed_predictions,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "correct_items": correct_items,
        "false_items": false_items,
        "missed_items": missed_items
    }

    return report

def save_report(output_file, report):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


json_file = "ptoutput/1117.json"
article_id = json_file.replace(".json", "").replace("ptoutput/", "")

manual_review = get_manual_review( "data/pretreatment_data.csv", article_id )
llm_review = get_llm_review(json_file)

report = compare(manual_review,llm_review)
save_report("testfile",report)




### Helper functions not in use

def list_filters():
    with open("data/pretreatment_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=";")
        pretreatment_filters = []
        for row in reader:
            filter = row[7]
            if filter not in pretreatment_filters:
                pretreatment_filters.append(filter)
        pretreatment_filters.pop(0)
        return pretreatment_filters


def get_manual_list(csv_file):
    results = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f,delimiter=";")
        for row in reader:
            doi = str(row[5])
            id = get_article_id(doi)
            if id != 0:
                datapoint = [id,row[7]]
                if datapoint not in results:
                    results.append(datapoint)
    return results