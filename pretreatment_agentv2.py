import glob
import json
import logging
import re
import time

from datetime import datetime
from Models import qwen_prompt, gemma_prompt, lfm_prompt

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
def setup_logger(run_id):
    log_filename = f"logs/{datetime.now().strftime('%m-%d_%H-%M')}_{run_id}.log"

    logger = logging.getLogger(run_id)
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(console_handler)

    return logger

def run_pretreatment_identification(path, run_id,logger,llm_prompt,reasoning):
    logger.info(path)
    article_text = read_file(path)
    article_title = article_text.splitlines()[0]
    temp_name = str(path).replace(".txt", "").replace("articletxt/", "")
    prompt = article_text + "\n" + pretreatment_identification_prompt
    logger.info(article_title+" Title of processing article")
    response = llm_prompt(prompt,reasoning)[0]
    logger.info(response)
    response = response.strip()
    response = re.sub(r"^```json\s*", "", response)
    response = re.sub(r"\s*```$", "", response)

    article_path =  f"pretreatment_v2/primarylist_{run_id}_{temp_name}.json"
    try:
        data = json.loads(response)
        with open(article_path, 'w') as f:
            json.dump(data, f, indent=2)
        results=identify_question(article_path,llm_prompt,reasoning)
        results_path = article_path.replace("primarylist_", "result_")
        jsonfile = {
            "filters": results,
            "article_path": path,
            "article_title": article_title,
        }
        with open(results_path, 'w') as f:
            json.dump(jsonfile, f, indent=2)
    except json.JSONDecodeError as e:
        logger.error(f"LLM did not return valid JSON {e}. Response: {response}")

def identify_question(path,llm_prompt,reasoning):
    with open(path, 'r') as file:
        descriptions_text = json.load(file)
    descriptions_list = descriptions_text.get("pretreatments")

    results = []
    for des in descriptions_list:
        prompt = f"1.{des}\n2.{pretreatment_questions}\n{identify_categories_prompt}"
        output = llm_prompt(prompt,reasoning)
        results.append({
            "reasoning": output[1].strip(),
            "answer": output[0].strip()
        })
    return results


def run_pretreatment_v2(run_id,llm_prompt,reasoning=False):
    logger = setup_logger(run_id)
    logger.info("start")
    start = time.time()
    count=0

    for article in articles_list:
        count += 1
        run_pretreatment_identification(article,run_id,logger,llm_prompt,reasoning)

    end = time.time()
    logger.info("end")
    logger.info(f"{int(end - start)}: total time in seconds")
    logger.info(f"{((end - start) / 3600)}: total time in hours")
    logger.info(f"{((end - start) / count / 60)}: time per article in minutes")


run_pretreatment_v2("v2-1006-qwen3.5", qwen_prompt)
run_pretreatment_v2("v2-1006-gemma3", gemma_prompt)
run_pretreatment_v2("v2-1006-lfm2.5", lfm_prompt)

