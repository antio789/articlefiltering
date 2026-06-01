import glob
import json
import logging

from ollama import generate
from pypdf import PdfReader
from datetime import datetime

logger = logging.getLogger(__name__)

'''READ CONTENT DEFINITIONS'''

def read_json(path):
    with open(path, 'r') as file:
        data = json.load(file)
    return data.get("questions")


def read_file(path):
    with open(path, 'r') as file:
        output = file.read()
    return output

# models tested mistral, ministral, mistrallite, nemotron, qwen, gemma3n:e2b.
# ministral-3:8b: too large, 4k context maximum for 8gb vram
# gemma 3, fastest can go up to 128k, 86k to leave space to increase output size  - gemmatest86k
# qwen3.5, reasoning model, but at a slower speed and smaller context, requires analysis with larger vram and faster GPU
def llm_prompt(string):
    response = generate(model='qwen40x2k', prompt=string,
                        options={ 'num_predict': 10000, 'seed': 15,"think": True})
    time = int(int(response['total_duration']) / 1000000000)
    logger.info(f'{time} seconds of runtime')
    return [response['response'],response['thinking']]


'''INITIALIZING CONTENT'''
pretreatment_identification_prompt = read_file("prompts/pretreatment_prefilter")
article_prompt = read_file("prompts/article_prompt")
article_questions = read_json('prompts/q_articles.json')

articles_list = glob.glob("articletxt/*.txt")

'LLM FILTERING'


def classify_article(text_to_classify):
    filter_list = []
    filter_list = filter_list + process_questions(article_questions, text_to_classify, article_prompt)
    return filter_list


def process_questions(questionnaire, text, prompt):
    results = []
    for section in questionnaire:
        if section.get("type") == "pretreatment" or section.get("type") == "improvements":
            for q in section.get("questions"):
                logger.info(q.get("qid"))
                prompt_question = "Article to read:\n" + text + "\nquestion:\n" + section.get(
                    "Additional_info") + "\n" + q.get("question") + ' \n' + prompt
                output = llm_prompt(prompt_question)
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

def run_pretreatmentarticle(path):
    logger.info(path)
    article_text = read_file(path)
    article_title = article_text.splitlines()[0]
    logger.info(article_title)
    filtered = classify_article(article_text)
    tempname = str(path).replace(".txt", "").replace("articletxt/", "")

    name = 'ptoutput/' + tempname + '.json'
    filtered.append({
        "article_title": article_title
    })
    jsonfile = {
        "filters": filtered,
        "article_path": path
    }
    with open(name, 'w') as f:
        json.dump(jsonfile, f, indent=2)

def run_pretreatment():
    logger.info('start')
    for path in articles_list:
        run_pretreatmentarticle(path)
    logger.info('end')

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs/{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])
run_pretreatment()
#print(run_pretreatmentarticle('articletxt/1832.txt'))