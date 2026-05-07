from ollama import chat, generate
from pip._internal.utils import datetime
from pypdf import PdfReader
import json
import glob
import tiktoken
import logging

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

#models tested mistral, ministral, mistrallite, nemotron, qwen, gemma3n:e2b.
# ministral-3:8b: too large, 4k context maximum for 8gb vram
# gemma 3, fastest can go up to 128k, 86k to leave space to increase output size  - gemmatest86k
# qwen3.5, reasoning model, but at a slower speed and smaller context requires deeper analysis qwen
def llm_prompt(string):
    response = generate(model='gemmatest86k', prompt=string, options={'temperature':0,'num_predict':12000,'seed':15})
    time = int(int(response['total_duration'])/1000000000)
    logger.info(time)
    print(str(time) + ' seconds of runtime')
    return response['response']


#testing function to predict token utilisation by input
def count_tokens(text, model="gpt-4"):
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))


'''INITIALIZING CONTENT'''
general_prompt = read_file("general_prompt")
article_prompt = read_file("article_prompt")
review_prompt = read_file("review_prompt")

general_questions = read_json('q_general.json')
review_filters = read_json('q_reviews.json')
article_filters = read_json('q_articles.json')

articles_list = glob.glob("articles/*.pdf")

#article_text = read_pdf(articles_list[0])


'LLM FILTERING'
def classify_article(text):
    print(text)
    filter_list = []
    #askes the main questions: 1.if its anaerobic digestion otherwise return, 2.if it's a review
    for i in general_questions:
        general_prompt = "Article to read:\n" + text + "\nquestion:\n" + i.get("question") + ' \n'+ general_prompt
        general_response = llm_prompt(general_prompt)
        general_response.lower()
        print(general_response)
        general_reasoning, general_answer = general_response.split("###")
        filter_list.append({
            "qid": i.get("qid"),
            "question": i.get("question"),
            "reasoning": general_reasoning.strip(),
            "answer": general_answer.strip()
        })
        if i == 0 and "false" in general_answer:
            return filter_list
    #splits the questions in between reviews and articles as the prompt is slightly different, true means review
    filters = article_filters
    filter_prompt = article_prompt
    logger.info("Review article:" + filter_list[1]["answer"].lower())
    if "true" in filter_list[1]["answer"].lower():
        filters = review_filters
        filter_prompt = review_prompt

    for q in filters:
        logger.info(q.get("qid"))
        prompt_question = "Article to read:\n" + text + "\nquestion:\n" + q.get("question") + ' \n' + filter_prompt
        output = llm_prompt(prompt_question)
        print(output)
        review_reasoning, review_answer = output.split("###")
        logger.info(str(q.get("qid")) + str(review_reasoning))
        filter_list.append({
            "qid": q.get("qid"),
            "question": q.get("question"),
            "reasoning": review_reasoning.strip(),
            "answer": review_answer.strip()
        })

    if "true" in filter_list[1]["answer"].lower():
        print("review")
        for q in review_filters:
            print(q.get("qid"))
            prompt_question = "Article to read:\n" + text + "\nquestion:\n" + q.get("question") + ' \n' + review_prompt
            output = llm_prompt(prompt_question)
            print(output)
            review_reasoning, review_answer = output.split("###")
            logger.info(str(q.get("qid")) + str(review_reasoning))
            filter_list.append({
                "qid": q.get("qid"),
                "question": q.get("question"),
                "reasoning": review_reasoning.strip(),
                "answer": review_answer.strip()
            })
    else:
        print("article")
        for q in article_filters:
            print(q.get("qid"))
            prompt_question = "Article to read:\n" + text + "\nquestion:\n" + q.get("question") + ' \n' + article_prompt
            output = llm_prompt(prompt_question)
            print(output)
            article_reasoning, article_answer = output.split("###")
            logger.info(str(q.get("qid"))+ str(article_reasoning))
            filter_list.append({
                "qid": q.get("qid"),
                "question": q.get("question"),
                "reasoning": article_reasoning.strip(),
                "answer": article_answer.strip()
            })
    return filter_list

def process_question(questionnaire,text,prompt):
    results = []
    for q in questionnaire:
        logger.info(q.get("qid"))
        prompt_question = "Article to read:\n" + text + "\nquestion:\n" + q.get("question") + ' \n' + prompt
        output = llm_prompt(prompt_question)
        logger.info(output)
        try:
            reasoning, answer = output.split("###")
            results.append({
                "qid": q.get("qid"),
                "question": q.get("question"),
                "reasoning": reasoning.strip(),
                "answer": answer.strip()
            })
        except ValueError as e:
            logger.warning(f'failed at splitting: f{e}, moving to next question')
    return results

'num_predict allows for changing output context length, need specific model, qwen currently best option but not sufficiently precise'
def clean_article(text):
    prompt = '''
    this is a science article that has been converted from pdf to text.
    The format needs to be corrected due to the conversion process.
    The only parts of importance are the title, the methodology and further discussion. Do omit The abstract, introduction, conclusion and references.
    Note that review articles might not have a clear methodology or discussion, but consider then the main text body without the omitted parts.
    Clearly mark the different sections ex: [title].
    Please do not change the text beyond the formatting process.
    Do not write any commentary
    '''
    prompt2 = "of this scientific article please return ONLY the line number of where the reference start, much appreciated"
    #print(text+ "\n"+prompt2)
    text_prompt = text+ "\n"+prompt2

#qwen48k(maximum size) - gemma3.128k
    response = generate(model='qwen48k', prompt=text_prompt, options={'temperature':0,'num_predict':48000},)
    logger.info(response['think'])
    return response['response']

    #print(count_tokens(prompt))
    #print(prompt_questions)
    #llm_prompt(prompt_questions)

def run_filtering():
    logger.info('start')
    for art in articles_list:
        article_text = read_pdf(art)
        filtered = classify_article(article_text)
        tempname = str(art).replace(".pdf", "")
        tempname = tempname.replace("articles/", "")
        name= 'article_'+tempname+'.json'
        filtered.append({
            "article_path": art
        })
        jsonfile={
            "filters": filtered,
            "article_path": art
        }
        with open(name, 'w') as f:
            json.dump(jsonfile, f, indent=2 )
    logger.info('end')

def run_oneQ(id, text):
    qid=id-1
    if qid==43:
        print("note id 43 is not present")
        return
    if id>len(review_filters)+1:
        print("outside scope")
        return
    if qid>43: qid=qid-1
    print(review_filters[qid].get("qid"))
    prompt_question = "Article to read:\n" + text + "\nquestion:\n" + review_filters[qid].get("question") + ' \n' + review_prompt
    output = llm_prompt(prompt_question)
    print(output)

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs{datetime.now().strftime('%d %H:%M')}.log"), logging.StreamHandler()])
run_filtering()