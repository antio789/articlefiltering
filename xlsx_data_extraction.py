import csv
import glob
import json
import os


### Gathering the filters obtained from the manual filtering for the article list

#should ignore what is not in this list like freezing
pretreatment_map = {
    1: "mechanical disintegration",
    2: "thermal",#might need clear definition of what thermal means, like termperature of water bath shouldnt be included.
    3: "ultrasonic",
    4: "pressure",#might need some better definition, as includes thermal or ultrasonic methods as well as pressure to seperate liquid from solid
    5: "electric",#modify the question to inluce electrolysis more directly
    6: "alkaline",
    7: "acidic",
    8: "oxidizer",
    9: "solvent",
    10: "other",
    11: "enzyme",
    12: "fungi",
    13: "microbial consortium",#figure out what to do with ensilage proably exclude it
    14: "biological active substrate",
    15: "nanoparticles",
    16: "disinhibition",
    17: "chelating",
    18: "nutrient",
    58: "microaerobic"
}

def get_manual_review_article(artid): #Make sure there are no duplicates in the filtering list
    doi = ""
    with open("data/articlelist.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f,delimiter=";")
        for row in reader:
            if artid == str(row[1]):
                doi=row[2]
                break
        if doi == "":
            raise Exception(f"Error article not found for id: {artid}")
    results = []
    with open('data/pretreatment_complete_list.csv',encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if doi == row[5]:
                pretreatment = row[7].strip().lower()
                datapoint = [artid, pretreatment]
                if datapoint not in results and pretreatment in pretreatment_map.values():
                    results.append(datapoint)
    return results



### Gather results from the LLM filtering on the article list

def get_llm_review(jfile,art_id):
    results = []
    with open(jfile, 'r', encoding='utf-8') as file:
        data = json.load(file)
        filters = data.get("filters")
        for item in filters:
            answer = str(item.get("answer")).lower()
            if "true" in answer:
                qid = item.get("qid")
                pretreatment = pretreatment_map[qid]
                datapoint = [art_id, pretreatment]
                results.append(datapoint)
    return results

### Compare results from both sources

def compare(manual, llm, include_other=False):
    if include_other:
        manual_filtered = manual
        llm_filtered = llm
    else:
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
        precision = ( correct_predictions / (correct_predictions + false_predictions))
    if (correct_predictions + missed_predictions) > 0:
        recall = (correct_predictions / (correct_predictions + missed_predictions))
    if (precision + recall) > 0:
        f1_score = (2 * precision * recall / (precision + recall))

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

def compare_summary(manual, llm, include_other=False):
    if include_other:
        manual_filtered = manual
        llm_filtered = llm
    else:
        manual_filtered = [item for item in manual if item[1] != pretreatment_map[10]]
        llm_filtered = [item for item in llm if item[1] != pretreatment_map[10]]

    correct_predictions = 0
    false_predictions = 0
    missed_predictions = 0

    for item in llm_filtered:
        if item in manual_filtered:
            correct_predictions += 1
        else:
            false_predictions += 1

    for item in manual_filtered:
        if item not in llm_filtered:
            missed_predictions += 1

    precision = 0
    recall = 0
    f1_score = 0

    if (correct_predictions + false_predictions) > 0:
        precision = (correct_predictions / (correct_predictions + false_predictions))
    if (correct_predictions + missed_predictions) > 0:
        recall = (correct_predictions / (correct_predictions + missed_predictions))
    if (precision + recall) > 0:
        f1_score = (2 * precision * recall / (precision + recall))

    return {
        "correct_predictions": correct_predictions,
        "false_predictions": false_predictions,
        "missed_predictions": missed_predictions,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4)
    }

def compare_question(question_name, all_manual, all_llm):

    manual_filtered = [
        item for item in all_manual
        if item[1] == question_name
    ]

    llm_filtered = [
        item for item in all_llm
        if item[1] == question_name
    ]

    return compare(
        manual_filtered,
        llm_filtered,
        include_other=True
    )

def run_all():
    ensure_results_dirs()

    json_files = glob.glob("ptoutput/*.json")

    all_manual = []
    all_llm = []

    for article_output in json_files:
        processing_id = (os.path.basename(article_output).replace(".json", ""))
        print(processing_id + " article id check")

        manual_review = get_manual_review_article(processing_id)
        llm_review = get_llm_review(article_output,processing_id)

        article_report = compare(manual_review, llm_review, include_other=False)
        save_report(f"results/articles/{processing_id}.json", article_report)

        all_manual.extend(manual_review)
        all_llm.extend(llm_review)

    global_report = compare_summary(all_manual, all_llm, include_other=False)
    save_report("results/all/global_report_2205_1430.json", global_report)

    for qid, question_name in pretreatment_map.items():
        question_report = compare_question(question_name, all_manual, all_llm)

        filename = f"results/questions/questions_{qid}.json"
        save_report(filename, question_report)

    print("Finished")


### file handling

def save_report(output_file, report):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


def ensure_results_dirs():
    os.makedirs("results/all", exist_ok=True)
    os.makedirs("results/articles", exist_ok=True)
    os.makedirs("results/questions", exist_ok=True)



### Run

#87 should be checked as missing some pretreatments
run_all()


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


