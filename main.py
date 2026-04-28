from ollama import chat
from ollama import ChatResponse
from pypdf import PdfReader
import json
import glob
import tiktoken
import fitz

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

def pdf_img(path):
    doc = fitz.open(path)
    images= []

    for page in doc:
        pix = page.getPixmap(matrix=fitz.Matrix(2,2))
        imgB = pix.tobytes("png")
        images.append(imgB)
    return images

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
  print(response.message.content)

def count_tokens(text, model="gpt-4"):
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))


'''INITIALIZING CONTENT'''
general_prompt = rf("general_prompt")
article_prompt = rf("article_prompt")
review_prompt = rf("review_prompt")

general_questions = json_read('q_general.json')
filters = json_read('q_filtering.json')

articles_list = glob.glob("articles/*.pdf")

article_text = pdf_read(articles_list[0])
print('article read')

'PDF ARRANGING'


'FILTERING'
for i in general_questions:
    prompt = "Article to read:\n" + article_text + "\nquestion:\n" + i.get("question") + ' \n'+ general_prompt
    #llm_prompt(prompt)

prompt_questions = "Article to read:\n" + article_text + "\nquestion:\n" + filters[0].get("question") + ' \n'+ review_prompt
#print(count_tokens(prompt))
#print(prompt_questions)
#llm_prompt(prompt_questions)
