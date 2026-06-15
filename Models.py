# models tested mistral, ministral, mistrallite, nemotron, qwen, gemma3n:e2b.
# ministral-3:8b: too large, 4k context maximum for 8gb vram
# gemma 3:4b, fastest can go up to 128k, 86k to leave space to increase output size  - gemmatest86k
# qwen3.5:2.3b, reasoning model, works better but much smaller and tends to run out of context due to looping reasoning: qwen40x2k
# lfm2.5:8b
import ollama
from ollama import generate

#qwen has a issue with looping reasoning
#default values: num_predict': 15000 presence_penalty 1.5 temperature 1 top_k 20 top_p 0.95
def qwen_prompt(prompt, reasoning=False):
    response = generate(model='qwen40x2k', prompt=prompt,
                        options={ 'num_predict': 15000,"presence_penalty":1.5,"repeat_penalty": 1.1,"top_k":30,'top_p':0.95,"min_p":0.1,"temperature":1, 'seed': 15},
                        think=reasoning)
    if reasoning:
        return [response['response'],response['thinking']]
    return [response['response'],""]


def gemma_prompt(string,reasoning=False):
    response = generate(model='gemmatest86k', prompt=string,
                        options={ 'num_predict': 2000, 'seed': 15,'temperature':0.1})
    return [response['response'],""]


def lfm_prompt(string,reasoning=False):
    response = generate(model='lfm80k', prompt=string,
                        options={ 'num_predict': 15000, 'seed': 15},think=reasoning)
    if reasoning:
        return [response['response'], response['thinking']]
    return [response['response'], ""]


