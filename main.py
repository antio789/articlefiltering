from ollama import chat
from ollama import ChatResponse
from pypdf import PdfReader
import json
import glob
import tiktoken

'''READ CONTENT DEFINITIONS'''
def json_read(path):
    with open(path, 'r') as file:
        data = json.load(file)  # Load the JSON data into a Python list
    return data.get("questions")

def rf(path):
  with open(path, 'r') as file:
    output = file.read()
  return output

def pdf_read(path):
    reader = PdfReader(path)
    return "\n".join(p.extract_text() for p in reader.pages)

def llm_prompt(string):
  response: ChatResponse = chat(model='mistral', messages=[
    {
      'role': 'user',
      'content': string,
    },
  ])
  print(response.message.content)

def count_tokens(text, model="gpt-4"):
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))


'''INITIALIZING CONTENT'''
general_prompt = rf("general_prompt")
article_prompt = rf("article_prompt")
review_prompt = rf("review_prompt")

general_questions = json_read('q_general.json')

articles_list = glob.glob("articles/*.pdf")

article_text = pdf_read(articles_list[0])


'FILTERING'
prompt = general_prompt + "\nquestion:\n" + general_questions[0].get("question") + "\nArticle to read:\n" + article_text
#print(prompt)
#llm_prompt(prompt)
#print(count_tokens(prompt))

