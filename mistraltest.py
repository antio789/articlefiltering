import glob
import json
import logging
import os
import re
from datetime import datetime
from time import sleep

from mistralai.client import Mistral


logger = logging.getLogger(__name__)

def mistral_prompt(question):
    with Mistral(api_key=os.getenv("MISTRAL_API_KEY", ""),) as mistral:
        res = mistral.chat.complete(model="mistral-small-2603",temperature=0.1,reasoning_effort="high",random_seed=15,max_tokens=5000, messages=[
            {
                "role": "user",
                "content": question,
            },
        ], stream=False, response_format={
            "type": "text",
        })
    # Handle response
    sleep(2)
    return res.choices[0].message.content

def read_json(path):
    with open(path, 'r') as file:
        data = json.load(file)
    return data.get("questions")


def read_file(path):
    with open(path, 'r') as file:
        output = file.read()
    return output

article_prompt = read_file("prompts/article_prompt")
article_questions = read_json('prompts/q_articles.json')
pretreatment_identification_prompt = read_file("prompts/pretreatment_prefilter")

articles_list = glob.glob("articletxt/*.txt")

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
                output = mistral_prompt(prompt_question)
                logger.info(output)

                results.append({
                    "qid": q.get("qid"),
                    "question": q.get("question"),
                    "reasoning": "",
                    "answer": output.strip()
                })
    return results


def run_pretreatmentarticle(path):
    logger.info(path)
    article_text = read_file(path)
    filtered = classify_article(article_text)
    tempname = str(path).replace(".txt", "").replace("articletxt/", "")

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

def run_pretreatment_identification(path):
    logger.info(path)
    article_text = read_file(path)

    tempname = str(path).replace(".txt", "").replace("articletxt/", "")
    prompt = article_text + "\n" + pretreatment_identification_prompt
    response = mistral_prompt(prompt)[1].text
    print(response)
    response = response.strip()
    response = re.sub(r"^```json\s*", "", response)
    response = re.sub(r"\s*```$", "", response)

    name =  tempname + '.json'
    data = json.loads(response)
    with open(name, 'w') as f:
        json.dump(data, f, indent=2)

def identify_question(path):
    identify = read_file("prompts/selectfromlist")
    with open(path, 'r') as file:
        descriptions_text = json.load(file)
    descriptions_list = descriptions_text.get("pretreatments")
    for des in descriptions_list:
        prompt = f"{des}\n{descriptions_list}\n{identify}"
        response = mistral_prompt(prompt)
        answer = response[1].text
        reasoning = response[0].thinking


        print(answer)
        print(reasoning)


logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs/{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])
#run_pretreatment_identification("articletxt/2.txt")
identify_question("2.json")
"""
[
    ThinkChunk
        (
            thinking=
                [
                    TextChunk
                        (
                            text='Okay'
                            type='text'
                        )
                ], 
                    type='thinking', 
                    signature=Unset(), closed=True
        ), 
    TextChunk(
        text='-1', 
        type='text')
]
"""