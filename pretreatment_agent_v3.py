import ast
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
filtering_prompt = read_file('prompts/onestepidentification')

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

def run_filtering(run_id):
    for article in articles_list:
        logger.info(article)
        article_text = read_file(article)
        article_title = article_text.splitlines()[0]
        logger.info("Title of processing article: "+article_title  )
        prompt = f"1.Article Text:\n {article_text}\n\n2.Filtering Questions:\n{pretreatment_questions}\n\n3.Task:\n{filtering_prompt}"
        output = llm_prompt(prompt)
        response = output[0].strip()
        temp_name = str(article).replace(".txt", "").replace("articletxt/", "")
        article_path = f"pretreatment_v3/results_{temp_name}_{run_id}.json"
        jsonfile = {
            "filters": ast.literal_eval(response),
            "article_path": article,
            "article_title": article_title,
            "prompt": filtering_prompt,
            "reasoning":output[1]
        }
        with open(article_path, 'w') as f:
            json.dump(jsonfile, f, indent=2)


logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs/{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])

run_filtering("v3-0206-1800")