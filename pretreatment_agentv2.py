import glob
import json
import logging
import re

from ollama import generate
from datetime import datetime


'''READ CONTENT DEFINITIONS'''
def read_json(path):
    with open(path, 'r') as file:
        data = json.load(file)
    return data.get("questions")


def read_file(path):
    with open(path, 'r') as file:
        output = file.read()
    return output


'''INITIALIZING CONTENT'''
pretreatment_questions = read_json('prompts/q_articles_v2.json')[0].get('questions')
pretreatment_identification_prompt = read_file("prompts/pretreatment_prefilter")
identify_categories_prompt = read_file("prompts/selectfromlist")

articles_list = glob.glob("articletxt/*.txt")

'''FILTERING CONTENT'''
logger = logging.getLogger(__name__)

def llm_prompt(string):
    response = generate(model='qwen40x2k', prompt=string,
                        options={ 'num_predict': 20000, 'seed': 15,"think": True})
    time = int(int(response['total_duration']) / 1000000000)
    logger.info(f'{time} seconds of runtime')
    logger.info(response['thinking'])
    logger.info(response['response'])
    return [response['response'],response['thinking']]

def run_pretreatment_identification(path, run_id):
    logger.info(path)
    article_text = read_file(path)
    article_title = article_text.splitlines()[0]
    temp_name = str(path).replace(".txt", "").replace("articletxt/", "")
    prompt = article_text + "\n" + pretreatment_identification_prompt
    logger.info(article_title+" Title of processing article")
    response = llm_prompt(prompt)[0]
    response = response.strip()
    response = re.sub(r"^```json\s*", "", response)
    response = re.sub(r"\s*```$", "", response)

    article_path =  f"pretreatment_v2/primarylist_{temp_name}_{run_id}.json"
    try:
        data = json.loads(response)
        with open(article_path, 'w') as f:
            json.dump(data, f, indent=2)
        results=identify_question(article_path)
        results_path = article_path.replace("primarylist_", "result_")
        jsonfile = {
            "filters": results,
            "article_path": path,
            "article_title": article_title,
        }
        with open(results_path, 'w') as f:
            json.dump(jsonfile, f, indent=2)
    except json.JSONDecodeError as e:
        logger.error(f"LLM did not return valid JSON. Response: {response}")

def identify_question(path):
    with open(path, 'r') as file:
        descriptions_text = json.load(file)
    descriptions_list = descriptions_text.get("pretreatments")

    results = []
    for des in descriptions_list:
        prompt = f"1.{des}\n2.{pretreatment_questions}\n{identify_categories_prompt}"
        output = llm_prompt(prompt)
        results.append({
            "reasoning": output[1].strip(),
            "answer": output[0].strip()
        })
    return results


def run_pretreatment_v2(run_id):
    for article in articles_list:
        run_pretreatment_identification(article,run_id)

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs/{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])

run_pretreatment_v2("0206-1800")


