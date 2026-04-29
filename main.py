from ollama import chat, generate
from ollama import ChatResponse
from pypdf import PdfReader
import json
import glob
import tiktoken
import fitz
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
    response = generate(model='qwen48k', prompt=string, options={'temperature':0,'num_ctx':42000,'num_predict':12000})
    time = int(response['total_duration'])/1000000
    logger.info(time)
    print(time + 'time to run in seconds')
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

article_text = read_pdf(articles_list[0])


'LLM FILTERING'
def classify_article(text):
    filter_list = []
    #askes the main questions: 1.if its anaerobic digestion otherwise return, 2.if it's a review
    for i in general_questions:
        prompt = "Article to read:\n" + text + "\nquestion:\n" + i.get("question") + ' \n'+ general_prompt
        response = llm_prompt(prompt)
        response.lower()
        print(response)
        reasoning, answer = response.split("###")
        filter_list.append(answer)
        if i == 0 and "false" in answer:
            return filter_list
    #splits the questions in between reviews and articles as the prompt is slightly different, true means review
    if "true" in filter_list[1]:
        print("review")
        for q in review_filters:
            print(q.get("qid"))
            prompt_question = "Article to read:\n" + text + "\nquestion:\n" + q.get("question") + ' \n' + review_prompt
            output = llm_prompt(prompt_question)
            print(output)
            filter_list.append(output)
    else:
        print("article")
        for q in article_filters:
            print(q.get("qid"))
            prompt_question = "Article to read:\n" + text + "\nquestion:\n" + q.get("question") + ' \n' + article_prompt
            output = llm_prompt(prompt_question)
            print(output)
            filter_list.append(output)
    return filter_list

'num_predict allows for changing output context length, need specific model'
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
    prompt2 = "Of this scientific article extract only the methodology section. return ONLY the extracted text, with no commentary, explanations, or formatting"
    #print(text+ "\n"+prompt2)
    text_prompt = text+ "\n"+prompt

#qwen48k(maximum size) - gemma3.128k
    response = generate(model='qwen48k', prompt=text_prompt, options={'num_predict':48000,'num_ctx':48000})
    return response['response']

    #print(count_tokens(prompt))
    #print(prompt_questions)
    #llm_prompt(prompt_questions)

logging.basicConfig(filename='llmlog.log',format='%(asctime)s %(message)s',level=logging.INFO)
logger.info('start')
filtered = classify_article(article_text)
print(filtered)
with open('filtered_articles', 'w') as outfile:
    outfile.write(str(filtered))
logger.info('end')