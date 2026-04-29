from ollama import chat
from ollama import ChatResponse
from pypdf import PdfReader
import json
import glob
import tiktoken
import fitz
import logging

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
# ministral-3:8b: very fast and writes good reasoning, not very accurate, pretty dumb, forgets text.
# nemotron is very fast but not very smart
# gemma 3 very fast but unstable
def llm_prompt(string):
  response: ChatResponse = chat(model='ministral-3:8b', messages=[
    {
      'role': 'user',
      'content': string,
    },
  ])
  return response.message.content

#testing function to predict token utilisation by input
def count_tokens(text, model="gpt-4"):
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))


'''INITIALIZING CONTENT'''
general_prompt = read_file("general_prompt")
article_prompt = read_file("article_prompt")
review_prompt = read_file("review_prompt")

general_questions = read_json('q_general.json')
review_filters = read_json('q_articles.json')
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
        reasoning, answer = response.split("###")
        filter_list.append(answer)
        if i == 0 and answer == "false":
            return filter_list
    #splits the questions in between reviews and articles as the prompt is slightly different, true means review
    cleaned_article = clean_article(text)
    if filter_list[1] == "true":
        for q in review_filters:
            prompt_question = "Article to read:\n" + cleaned_article + "\nquestion:\n" + q.get("question") + ' \n' + review_prompt
            filter_list.append(prompt_question)
    else:
        for q in article_filters:
            prompt_question = "Article to read:\n" + cleaned_article + "\nquestion:\n" + q.get("question") + ' \n' + article_prompt
            filter_list.append(prompt_question)

def clean_article(text):
    prompt = '''
    this is a science article that has been converted from pdf to text.
    The format needs to be corrected due to the conversion process.
    The only parts of importance are the title, the methodology and further discussion. Do omit The abstract, introduction, conclusion and references.
    Clearly mark the different sections ex: [title].
    Please do not change the text beyond the formatting process. The text need to be further processed and modifications will hurt the accuracy.
    '''
    response: ChatResponse = chat(model='ministral-3:8b', messages=[
        {
            'role': 'user',
            'content': prompt
        },
    ])
    return response.message.content

    #print(count_tokens(prompt))
    #print(prompt_questions)
    #llm_prompt(prompt_questions)
print(clean_article(article_text))