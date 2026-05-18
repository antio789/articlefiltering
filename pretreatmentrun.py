import glob
import json
import logging
import os

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


def read_pdf(path):
    reader = PdfReader(path)
    return "\n".join(p.extract_text() for p in reader.pages)


# models tested mistral, ministral, mistrallite, nemotron, qwen, gemma3n:e2b.
# ministral-3:8b: too large, 4k context maximum for 8gb vram
# gemma 3, fastest can go up to 128k, 86k to leave space to increase output size  - gemmatest86k
# qwen3.5, reasoning model, but at a slower speed and smaller context, requires analysis with larger vram and faster GPU
def llm_prompt(string):
    response = generate(model='gemmatest86k', prompt=string,
                        options={'temperature': 0.1, 'num_predict': 12000, 'seed': 15})
    time = int(int(response['total_duration']) / 1000000000)
    logger.info(f'{time} seconds of runtime')
    return response['response']


'''INITIALIZING CONTENT'''
general_prompt = read_file("prompts/general_prompt")
article_prompt = read_file("prompts/article_prompt")
review_prompt = read_file("prompts/review_prompt")

general_questions = read_json('prompts/q_general.json')
review_questions = read_json('prompts/q_reviews.json')
article_questions = read_json('prompts/q_articles.json')

articles_list = glob.glob("pretreatmentarticles/*.pdf")

test = os.environ.get('elsevierapi', '5432')
os.environ['test'] = 'development'
'LLM FILTERING'


def classify_article(text):
    filter_list = []
    filter_list = filter_list + process_questions(article_questions, text, article_prompt)
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
                try:
                    reasoning, answer = output.split("###")
                except ValueError as e:
                    logger.warning(f'failed at splitting: f{e}, moving to next question')
                    reasoning = output
                    answer = "error"

                results.append({
                    "qid": q.get("qid"),
                    "question": q.get("question"),
                    "reasoning": reasoning.strip(),
                    "answer": answer.strip()
                })
    return results

def run_pretreatmentarticle(path):
    logger.info(path)
    article_text = read_pdf(path)
    filtered = classify_article(article_text)
    tempname = str(path).replace(".pdf", "").replace("pretreatmentarticles/", "")

    name = 'ptoutput/' + tempname + '.json'
    filtered.append({
        "article_path": path
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

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])
#run_pretreatment()
print(read_pdf("pretreatmentarticles/752.pdf"))