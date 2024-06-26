import json
import os
import random
import re
import pandas as pd
from typing import Dict
from collections import defaultdict

def create_prompt(prompt_type: str, prompt_template: str, subject_entity: str) -> str:
	if prompt_type == 'question':
		return prompt_template.replace('{subject_entity}', subject_entity)
	elif prompt_type == 'statement':
		return prompt_template.replace('{subject_entity}', subject_entity)

def create_fewshot(prompt_type: str, data_df: pd.DataFrame, relation: str, prompt_template: str) -> Dict:
   
    examples = defaultdict(str)
    # get rows with the same relation
    data_df = data_df[data_df['Relation'] == relation].copy()

    for idx, row in data_df[:5].iterrows():
        q = create_prompt(prompt_type, prompt_template, row['SubjectEntity'])
        # use double quotes for strings in the list to avoid SyntaxError
        a = '["' + '", "'.join(row['ObjectEntities']) + '"]'
        examples[q] = a
    return examples

def create_sample_fewshot(examples: Dict, n_samples = 3) -> str:
	if examples == {}:
		return ""
	fewshot = "Examples: "
	random_items = random.sample(examples.items(), n_samples)
	for q, a in random_items:
		fewshot += "Q: " + q + " A: " + a + " "
	return fewshot


def create_full_prompt(prompt_type: str, fewshot: str, query: str) -> str:
	add_query = ""
	if (prompt_type == "statement"):
		add_query = " {mask_token}"
	#instruction = "Format the response" + add_query + " as a Python list such as [\"answer_a\", \"answer_b\"]. The output should follow the exact format as the examples. Return a list with an empty string [\"\"] if no information is available. "
	instruction = "Format the response" + add_query + " as a Python list such as [\"answer_a\", \"answer_b\"]. The output should follow the exact format as the examples. "
	query = fewshot + instruction + "Q: " + query + " A:"
	return query

def extract_answers_response(response: str) -> list:
    match = re.search(r'\[(.*?)\]', response)
    if match:
        items = match.group(1).split(", ")
        return [item.strip('"') for item in items]
    else:
        return ['']

def create_explanation_prompt(query: str, output: list) -> str:
	instruction = "Your response to \"" + query + "\" was " + str(output) + ". How confident are you in this response and why? Please answer with a number between 0 and 1, where 0 indicates no confidence at all and 1 indicates maximum confidence."
	return instruction

def create_choose_option_prompt(query: str, relation: str) -> str:
	return "Given the following options and their description, what is the most probable option related with the relation \"" + relation + "\". Return only the corresponding number (e.g., 1).\n" + query
