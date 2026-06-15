import glob
import json
import logging
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
article_prompt = read_file("prompts/article_prompt")
article_questions = read_json('prompts/q_articles.json')

articles_list = glob.glob("articletxt/*.txt")

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

'LLM FILTERING'
def classify_article(text_to_classify,logger,model,reasoning):
    filter_list = []
    filter_list = filter_list + process_questions(article_questions, text_to_classify, article_prompt,logger,model,reasoning)
    return filter_list


def process_questions(questionnaire, text, prompt,logger,model,reasoning):
    results = []
    for section in questionnaire:
        if section.get("type") == "pretreatment":
            for q in section.get("questions"):
                logger.info(q.get("qid"))
                prompt_question = "Article to read:\n" + text + "\nquestion:\n" + section.get(
                    "Additional_info") + "\n" + q.get("question") + ' \n' + prompt
                output = model(prompt_question,reasoning)
                logger.info(output)
                """
                try:
                    reasoning, answer = output.split("###")
                except ValueError as e:
                    logger.warning(f'failed at splitting: f{e}, moving to next question')
                    reasoning = output
                    answer = "error"
                """
                results.append({
                    "qid": q.get("qid"),
                    "question": q.get("question"),
                    "reasoning": output[1].strip(),
                    "answer": output[0].strip()
                })
    return results

def run_pretreatmentarticle(path,run_id,logger,model,reasoning):
    logger.info(path)
    article_text = read_file(path)
    article_title = article_text.splitlines()[0]
    logger.info(article_title)
    filtered = classify_article(article_text,logger,model,reasoning)
    tempname = str(path).replace(".txt", "").replace("articletxt/", "")

    name = f"ptoutput/{run_id}_{tempname}.json"
    filtered.append({
        "article_title": article_title
    })
    jsonfile = {
        "filters": filtered,
        "article_path": path
    }
    with open(name, 'w') as f:
        json.dump(jsonfile, f, indent=2)

def run_pretreatment(run_id,model,reasoning=False):
    logger = setup_logger(run_id)

    logger.info("start")
    start = time.time()
    count = 0

    for path in articles_list:
        count+=1
        run_pretreatmentarticle(path,run_id,logger,model,reasoning)

    end = time.time()
    logger.info("end")
    logger.info(f"{int(end - start)}: total time in seconds")
    logger.info(f"{((end - start)/ 3600)}: total time in hours")
    logger.info(f"{((end - start) / count/60)}: time per article in minutes")

run_pretreatment("v1-0506-gemma", gemma_prompt)
run_pretreatment("v1-0506-qwen", qwen_prompt)
run_pretreatment("v1-0506-qwen-reason", qwen_prompt, reasoning=True)
run_pretreatment("v1-0506-lfm", lfm_prompt)
run_pretreatment("v1-0506-lfm-reason", lfm_prompt, reasoning=True)

