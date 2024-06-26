import argparse
import json
import time
import re
import os

from prompt import create_prompt, create_fewshot, create_full_prompt, create_sample_fewshot, extract_answers_response, create_explanation_prompt
from file_io import read_lm_kbc_jsonl_to_df, save_df_to_jsonl
from models import prompt_model, init_openai_key
from linkWikidata import find_wikidata
from collections import defaultdict, Counter
from gameui import choiceWindow

def main():
    parser = argparse.ArgumentParser(
        description="Arguments of input"
    )

    # Example llama: python main.py -mt llama -m llama-2-7b-chat.Q5_K_M.gguf -r CountryHasOfficialLanguage -d val -p question -fs True -ex True -mn True
    # Example gpt: python main.py -mt gpt -m gpt-3.5-turbo -r CountryHasOfficialLanguage -d val -p question -fs True -ex False -mn True
    # Example mistral: python main.py -mt mistral -m mistralai/Mistral-7B-Instruct-v0.2 -r CountryHasOfficialLanguage -d val -p question -fs True -ex False -mn True

    # model type can be gpt or llama
    parser.add_argument(
        "-mt",
        "--model_type",
        default="llama",
        type=str,
        required=True,
        choices=["llama", "gpt", "mistral"],
        help="Model Type"
    ) # model file name has to specified to run local or model name for API
    parser.add_argument(
        "-m",
        "--model",
        default="llama-2-7b-chat.Q5_K_M.gguf",
        type=str,
        required=True,
        help="Model"
    ) # prompting approach can be question or statement (add explanation flag in the future)
    parser.add_argument(
        "-p",
        "--prompt",
        default="question",
        type=str,
        required=True,
        choices=["question", "statement"],
        help="Prompting Approach"
    ) # relation between the subject entity and the objects
    parser.add_argument(
        "-r",
        "--relation",
        type=str,
        required=True,
        help="Relation between subject entity and objects"
    ) # dataset
    parser.add_argument(
        "-d",
        "--dataset",
        type=str,
        default="val",
        required=True,
        help="Dataset (validation as default)"
    ) # few shot or zero shot
    parser.add_argument(
        "-fs",
        "--fewshot",
        type=str,
        default="True",
        required=True,
        help="Toggle few shot examples"
    ) # explanation response
    parser.add_argument(
        "-ex",
        "--explanation",
        type=str,
        default="True",
        required=True,
        help="Toggle model response explanation"
    ) # manual mode
    parser.add_argument(
        "-mn",
        "--manual",
        type=str,
        default="False",
        required=False,
        help="Manual mode"
    ) # entity countet
    parser.add_argument(
        "-c",
        "--counter",
        type=str,
        default="False",
        required=False,
        help="Entity counter"
    )


    args = parser.parse_args()

    if (args.model_type == "gpt"):
        init_openai_key()

    relation_dict = {
        "BandHasMember": "P463",
        "CityLocatedAtRiver": "P206",
        "CompanyHasParentOrganisation": "P749",
        "CompoundHasParts": "P527",
        "CountryBordersCountry": "P47",
        "CountryHasOfficialLanguage": "P37",
        "CountryHasStates": "P150",
        "FootballerPlaysPosition": "P413",
        "PersonCauseOfDeath": "P509",
        "PersonHasAutobiography": "P50",
        "PersonHasEmployer": "P108",
        "PersonHasNoblePrize": "P527",
        "PersonHasNumberOfChildren": "P1971",
        "PersonHasPlaceOfDeath": "P20",
        "PersonHasProfession": "P106",
        "PersonHasSpouse": "P26",
        "PersonPlaysInstrument": "P1303",
        "PersonSpeaksLanguage": "P1412",
        "RiverBasinsCountry": "P205",
        "SeriesHasNumberOfEpisodes": "P1113",
        "StateBordersState": "P47"
    }

    # 1 - Data

    data_df = read_lm_kbc_jsonl_to_df('PythonApp/data/{}.jsonl'.format(args.dataset))
    data_df = data_df[data_df['Relation'] == args.relation].copy()

    # 2 - Prompting and Model

    # 2.1 - create prompts

    # question or statement
    if (args.prompt == "question"): 
        with open('PythonApp/question-prompts.json', 'r') as f:
            prompt_templates = json.load(f)
    elif (args.prompt == "statement"):     
        with open('PythonApp/statement-prompts.json', 'r') as f:
            prompt_templates = json.load(f)
    # find for specific relation
    prompt_template = prompt_templates[args.relation]


    # create few shot examples
    if (args.fewshot == "True"):
        train_df = read_lm_kbc_jsonl_to_df('PythonApp/data/train.jsonl')
        examples = create_fewshot(args.prompt, train_df, args.relation, prompt_template)
    else:
        examples = defaultdict(str)

    # 2.2. - Full prompts and send to model
    numSamples = 0
    correctSamples = 0
    explanation = ""
    results = []

    len_tiles = len(data_df)
    if (int(args.counter) <= len_tiles):
        curr_row = data_df.iloc[int(args.counter) - 1]
        query = create_prompt(args.prompt, prompt_template, curr_row['SubjectEntity'])
        sample_examples = create_sample_fewshot(examples)
        full_prompt = create_full_prompt(args.prompt, sample_examples, query)
        response = prompt_model(args.model_type, args.model, full_prompt) # prompt model with query
        output = extract_answers_response(response)
        output_str = ""
        for o in output:
            output_str += " " + str(o)
        #obj_ids = find_wikidata(output, relation_dict[args.relation])
        list_row = str(curr_row['SubjectEntityID']) + " " + str(relation_dict[args.relation]) + output_str
        print(list_row)
    else:
        print("False")

if __name__ == "__main__":
    main()
