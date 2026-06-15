import ast
import glob
import json
import logging

from datetime import datetime
import time

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
filtering_prompt = read_file('prompts/onestepidentification')

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

def run_filtering(run_id,llm_prompt,reasoning=False):
    logger = setup_logger(run_id)
    logger.info("start")
    start=time.time()
    count=0
    for article in articles_list:
        count+=1
        logger.info(article)
        article_text = read_file(article)
        article_title = article_text.splitlines()[0]
        logger.info("Title of processing article: "+article_title)
        if reasoning: prompt = f"1.Article Text:\n {article_text}\n\n2.Filtering Questions:\n{pretreatment_questions}\n\n3.Task:\n{filtering_prompt}"
        else: prompt = f"1.Article Text:\n {article_text}\n\n2.Filtering Questions:\n{pretreatment_questions}\n\n3.Task:\n{filtering_prompt_noreason}"
        output = llm_prompt(prompt,reasoning)
        response = output[0].strip()
        logger.info(response)
        logger.info(output[1])
        try:response = ast.literal_eval(response)
        except:
            logger.error(f"wrong format on the response: {response} for article: {article}")
            response=[]
        temp_name = str(article).replace(".txt", "").replace("articletxt/", "")
        article_path = f"pretreatment_v3/results_{run_id}_{temp_name}.json"
        jsonfile = {
            "filters": response,
            "article_path": article,
            "article_title": article_title,
            "prompt": filtering_prompt,
            "reasoning":output[1]
        }
        with open(article_path, 'w') as f:
            json.dump(jsonfile, f, indent=2)
    end = time.time()
    logger.info("end")
    logger.info(f"{int(end - start)}: total time in seconds")
    logger.info(f"{((end - start) / 3600)}: total time in hours")
    logger.info(f"{((end - start) / count / 60)}: time per article in minutes")

run_filtering("v3-1006-qwen3.5",qwen_prompt)
run_filtering("v3-1006-gemma3",gemma_prompt)
#run_filtering("v3-0506-qwen-reason",qwen_prompt,reasoning=True)
run_filtering("v3-1006-lfm2.5",lfm_prompt)
#run_filtering("v3-0506-lfm-reason",lfm_prompt,reasoning=True)