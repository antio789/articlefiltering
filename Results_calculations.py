import csv
import glob
import json
import os
import re

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

fixed_bed_subtypes = {
    "packed bed": "fixed bed",
    "anaerobic filter": "fixed bed",
    "fixed film": "fixed bed",
    "structured bed": "fixed bed"
}

uasb_subtypes = {
    "internal circulation": "uasb derivative",
    "induced bed": "uasb derivative",
    "upflow solid reactor": "uasb derivative",
    "compartmentalized anaerobic digester": "uasb derivative"
}

fluidized_bed_subtypes = {
    "expanded bed": "fluidized bed",
    "inverse turbulent bed": "fluidized bed",
    "moving bed": "fluidized bed"
}



combined_reactor_map = {
    20: "batch",
    21: "sequencing batch reactor",
    22: "cstr",
    23: "leach bed",
    24: "plug flow",
    25: "anaerobic contact reactor",
    26: "uasb",
    27: "egsb",
    28: uasb_subtypes,
    29: "baffled reactor",
    30: fixed_bed_subtypes,
    31: fluidized_bed_subtypes,
    32: "biofilm derivative",
    33: "membrane",
    34: "hybrid",
    35: "two stage",
    36: "small scale",
    37: "anaerobic lagoon",
    38: "other",
    39: "rotating disc / contactor",
    40: "gradual Concentric chambers reactor",
    41: "tower",
    42: "loop reactor",
    44: "hydraulic flush",
    45: "bionic reactor",
    46: "labyrinth flow reactor",
    47: "anaerobic self-flotation reactor"
}




def get_manual_review_article(artid): #Make sure there are no duplicates in the filtering list
    doi = ""
    with open("data/articlelist.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f,delimiter=";")
        for row in reader:
            if artid == int(row[1]):
                doi=row[2]
                break
        if doi == "":
            raise Exception(f"Error article not found for id: {artid}")
    results = []
    with open('data/pretreatment_0806.csv',encoding='utf-8') as f:
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
            if re.search(r'\btrue\b', answer):
                qid = item.get("qid")
                pretreatment = pretreatment_map[qid]
                datapoint = [art_id, pretreatment]
                if datapoint not in results:
                    results.append(datapoint)
    return results

def get_llmv2_review(jfile,art_id):
    results = []
    try:
        with open(jfile, 'r', encoding='utf-8') as file:
            data = json.load(file)
            filters = data.get("filters")
            for item in filters:
                    try:
                        qid = int(extract_integer(item.get("answer")))
                        if qid in pretreatment_map:
                            pretreatment = pretreatment_map[qid]
                            datapoint = [art_id,pretreatment]
                            if datapoint not in results:
                                results.append(datapoint)
                        elif qid != -1:
                            print(f"Wrong id for {art_id}: {item.get('answer')}")
                    except:
                        print(f"Wrong answer format on {art_id}: {item.get('answer')}")
    except:
        print(f"file not found: {jfile}")
    return results

def get_llmv3_review(jfile,art_id):
    results = []
    try:
        with open(jfile, 'r', encoding='utf-8') as file:
            data = json.load(file)
            filters = data.get("filters")
            if isinstance(filters,int):
                qid = filters
                if qid in pretreatment_map:
                    pretreatment = pretreatment_map[qid]
                    datapoint = [art_id, pretreatment]
                    if datapoint not in results:
                        results.append(datapoint)
            else:
                for item in filters:
                    try:
                        qid = item

                        if qid in pretreatment_map:
                            pretreatment = pretreatment_map[qid]
                            datapoint = [art_id, pretreatment]
                            if datapoint not in results:
                                results.append(datapoint)
                        elif qid != -1:
                            print(f"Wrong id for {art_id}: {item}")
                    except Exception as e:
                        print(f" {e}: {art_id}: {item}")
    except Exception as e:
        print(f"{e}: {jfile}")
    return results

def extract_integer(output):
    # Find all integers in the string
    numbers = re.findall(r'-?\d+', output)
    if numbers:
        return int(numbers[0])
    else:
        return -1

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
    manual_filtered = [item for item in all_manual if item[1] == question_name ]
    llm_filtered = [item for item in all_llm if item[1] == question_name]

    return compare_summary(manual_filtered, llm_filtered, include_other=True)

def calculate_pretreatment(runname,version=0):
    ensure_results_dirs()
    files = glob.glob("articletxt/*.txt")
    id_list = []
    for file in files:
        id_list.append(int(file.replace('articletxt/', '').replace('.txt', '')))
    folder_name = "ptoutput"
    files_path = f"{folder_name}/{runname}_"
    get_automated_review = get_llm_review
    if version == 2:
        folder_name = "pretreatment_v2"
        files_path = f"{folder_name}/result_{runname}_"
        get_automated_review = get_llmv2_review
    elif version == 3:
        folder_name = "pretreatment_v3"
        files_path = f"{folder_name}/results_{runname}_"
        get_automated_review = get_llmv3_review
    all_manual = []
    all_llm = []
    count=0
    for processing_id in id_list:
        count+=1

        manual_review = get_manual_review_article(processing_id)
        filepath = f"{files_path}{processing_id}.json"

        if not os.path.isfile(filepath):
            print(f"file not found for id: {processing_id}, filepath: {filepath} on {runname}")
            llm_review = []
        else: llm_review = get_automated_review(f"{files_path}{processing_id}.json", processing_id)
        article_report = compare(manual_review, llm_review, include_other=False)
        save_report(f"results/articles/{runname}_{processing_id}.json", article_report)

        all_manual.extend(manual_review)
        all_llm.extend(llm_review)

    global_report = compare_summary(all_manual, all_llm, include_other=False)
    save_report(f"results/all/{runname}.json", global_report)

    for qid, question_name in pretreatment_map.items():
        question_report = compare_question(question_name, all_manual, all_llm)

        filename = f"results/questions/questions_{runname}_{qid}.json"
        save_report(filename, question_report)
    print(count)
    print("Finished")


### file handling

def save_report(output_file, report):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


def ensure_results_dirs():
    os.makedirs("results/all", exist_ok=True)
    os.makedirs("results/articles", exist_ok=True)
    os.makedirs("results/questions", exist_ok=True)
def ensure_results_dirs_reactor():
    os.makedirs("results/all", exist_ok=True)
    os.makedirs("results/articles_reactor", exist_ok=True)
    os.makedirs("results/questions_reactor", exist_ok=True)


def get_manual_review_reactors(artdoi): #Make sure there are no duplicates in the filtering list
    results = []
    with open('data/reactors.csv',encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            doi = row[3].replace('http://dx.doi.org/','').replace("/",'_').strip()
            if artdoi == doi:
                reactor = row[19].strip().lower()

                if reactor == 'high rate':
                    reactor = row[20].strip().lower()
                for qid, category in combined_reactor_map.items():
                    if isinstance(category, str):
                        datapoint = [doi, category]
                        if reactor == category.lower() and datapoint not in results:
                            results.append(datapoint)
                    else:
                        if reactor in category:
                            mapped_value = category[reactor]
                            datapoint = [doi, mapped_value]
                            if datapoint not in results:
                                results.append(datapoint)
    return results

def get_llm_review_reactor(jfile,art_doi):
    results = []
    with open(jfile, 'r', encoding='utf-8') as file:
        data = json.load(file)
        filters = data.get("filters")
        for item in filters:
            answer = str(item.get("answer")).lower()
            if "true" in answer:
                qid = item.get("qid")
                if qid in combined_reactor_map:
                    reactor = combined_reactor_map[qid]
                    if isinstance(reactor, str):
                        datapoint = [art_doi, reactor]
                        if datapoint not in results: results.append(datapoint)
                    else:
                        main_category = list(reactor.values())[0]
                        datapoint = [art_doi, main_category]
                        if datapoint not in results:
                            results.append(datapoint)
    return results

def calculate_reactor(runname):
    ensure_results_dirs_reactor()

    json_files = glob.glob("reactoroutput/*.json")

    all_manual = []
    all_llm = []

    for reactor_output in json_files:
        processing_doi = (os.path.basename(reactor_output).replace(".json", ""))

        manual_review = get_manual_review_reactors(processing_doi)
        llm_review = get_llm_review_reactor(reactor_output,processing_doi)

        article_report = compare(manual_review, llm_review, include_other=True)
        save_report(f"results/articles_reactor/{runname}_{processing_doi}.json", article_report)

        all_manual.extend(manual_review)
        all_llm.extend(llm_review)

    global_report = compare_summary(all_manual, all_llm, include_other=True)
    save_report(f"results/all/global_reactor_{runname}.json", global_report)

    for qid, question_name in pretreatment_map.items():
        question_report = compare_question(question_name, all_manual, all_llm)

        filename = f"results/questions_reactor/questions_{runname}_{qid}.json"
        save_report(filename, question_report)

    print("Finished")

### Run
print("start comparison calculation")

calculate_pretreatment('v2-0806-gemma-reason',2)
calculate_pretreatment('v2-0806-qwen',2)
calculate_pretreatment('v2-0806-qwen-reason',2)
calculate_pretreatment('v2-0806-mistral',2)




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


