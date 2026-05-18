from ollama import generate
from pypdf import PdfReader
import json
import glob
import tiktoken
import logging
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

#models tested mistral, ministral, mistrallite, nemotron, qwen, gemma3n:e2b.
# ministral-3:8b: too large, 4k context maximum for 8gb vram
# gemma 3, fastest can go up to 128k, 86k to leave space to increase output size  - gemmatest86k
# qwen3.5, reasoning model, but at a slower speed and smaller context, requires analysis with larger vram and faster GPU
def llm_prompt(string):
    response = generate(model='gemmatest86k', prompt=string, options={'temperature':0.1,'num_predict':12000,'seed':15})
    time = int(int(response['total_duration'])/1000000000)
    logger.info(f'{time} seconds of runtime')
    return response['response']

#testing function to predict token utilisation by input
def count_tokens(text, model="gpt-4"):
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))

'''INITIALIZING CONTENT'''
general_prompt = read_file("prompts/general_prompt")
article_prompt = read_file("prompts/article_prompt")
review_prompt = read_file("prompts/review_prompt")

general_questions = read_json('prompts/q_general.json')
review_questions = read_json('prompts/q_reviews.json')
article_questions = read_json('prompts/q_articles.json')

articles_list = glob.glob("BRT_articles/*.pdf")

#article_text = read_pdf(articles_list[0])


'LLM FILTERING'
def classify_article(text):
    filter_list = []
    #asks the main questions: 1.if it's related to anaerobic digestion returns otherwise, 2.if it's a review
    filter_list = filter_list + process_questions(general_questions, text, general_prompt)
    if "false" in filter_list[0].get("answer"):
        return filter_list
    #splits the questions in between reviews and articles as the prompt is slightly different, true means review
    filters = article_questions
    filter_prompt = article_prompt
    logger.info("Review article:" + filter_list[1]["answer"].lower())
    if "true" in filter_list[1]["answer"].lower():
        filters = review_questions
        filter_prompt = review_prompt
    filter_list = filter_list + process_questions(filters, text, filter_prompt)
    return filter_list

def process_questions(questionnaire, text, prompt):
    results = []
    for section in questionnaire:
        for q in section.get("questions"):
            logger.info(q.get("qid"))
            prompt_question = "Article to read:\n" + text + "\nquestion:\n" +section.get("Additional_info")+"\n"+ q.get("question") + ' \n' + prompt
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
        run_article(art)
    logger.info('end')

def run_article(path):
    logger.info(path)
    article_text = read_pdf(path)
    filtered = classify_article(article_text)
    tempname = str(path).replace(".pdf", "")
    tempname = tempname.replace("articles/", "")
    name = 'article_' + tempname + '.json'
    filtered.append({
        "article_path": path
    })
    jsonfile = {
        "filters": filtered,
        "article_path": path
    }
    with open(name, 'w') as f:
        json.dump(jsonfile, f, indent=2)



def run_oneQ(questionid, text):
    qid= questionid - 1
    if qid==43:
        print("note id 43 is not present")
        return
    if questionid>58:
        print("outside scope")
        return
    if qid>43: qid=qid-1
    questiontext =""
    for section in review_questions:
        for q in section.get("questions"):
            if q.get("qid") == qid:
                questiontext = q.get("question")
                break
        if questiontext != "":
            break

    logger.info(review_questions[qid].get("qid"))
    prompt_question = "Article to read:\n" + text + "\nquestion:\n" + review_questions[qid].get("question") + ' \n' + review_prompt
    output = llm_prompt(prompt_question)
    logger.info(output)

def run_reviewquestions(id):
    text = read_pdf(articles_list[aID])
    logger.info(text)
    for question in range(1, 59):
        run_oneQ(question, text)



logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO, handlers=[logging.FileHandler(f"logs{datetime.now().strftime('%d_%H-%M')}.log"), logging.StreamHandler()])
#run_filtering()
for i in articles_list:
    print(i)
aID=0
arttext=read_pdf(articles_list[aID])
print(arttext)
run_article(articles_list[aID])