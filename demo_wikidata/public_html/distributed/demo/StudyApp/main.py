import argparse
import json
import time
import re
import os

from prompt import create_prompt, create_fewshot, create_full_prompt, create_sample_fewshot, extract_answers_response, create_explanation_prompt
from file_io import read_lm_kbc_jsonl_to_df, save_df_to_jsonl
from models import prompt_model, init_openai_key
#from linkWikidata import find_wikidata, list_wikidata_relation
from linkWikidata_mtabes import MTabES, find_wikidata
from collections import defaultdict, Counter
from gameui import choiceWindow
from sklearn.metrics import precision_score

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
    ) # LLM for linking
    parser.add_argument(
        "-lLLM",
        "--linkingLLM",
        type=str,
        default="False",
        required=False,
        help="LLM for Linking"
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

    data_df = read_lm_kbc_jsonl_to_df('data/{}.jsonl'.format(args.dataset))
    data_df = data_df[data_df['Relation'] == args.relation].copy()
    #objects_ids = list_wikidata_relation(args.relation)
    mtab_es = MTabES()

    # 2 - Prompting and Model

    # 2.1 - create prompts

    # question or statement
    if (args.prompt == "question"): 
        with open('question-prompts.json', 'r') as f:
            prompt_templates = json.load(f)
    elif (args.prompt == "statement"):     
        with open('statement-prompts.json', 'r') as f:
            prompt_templates = json.load(f)
    # find for specific relation
    prompt_template = prompt_templates[args.relation]


    # create few shot examples
    if (args.fewshot == "True"):
        train_df = read_lm_kbc_jsonl_to_df('data/train.jsonl')
        examples = create_fewshot(args.prompt, train_df, args.relation, prompt_template)
    else:
        examples = defaultdict(str)

    # 2.2. - Full prompts and send to model
    numSamples = 0
    correctSamples = 0
    explanation = ""
    results = []
    # for each subject entity in the data, create query and prompt the model
    for idx, row in data_df[:].iterrows():
        numSamples += 1
        query = create_prompt(args.prompt, prompt_template, row['SubjectEntity'])
        sample_examples = create_sample_fewshot(examples, 3)
        full_prompt = create_full_prompt(args.prompt, sample_examples, query)
        print("\nPrompt (" + args.prompt + ") to get answer:\n")
        print(full_prompt)
        print("\nSending prompt to model (" + args.model_type + ", " + args.model + ")...\n") 
        response = prompt_model(args.model_type, args.model, full_prompt) # prompt model with query
        output = extract_answers_response(response)
        print("Answer: " + str(row['SubjectEntity']) + " " + str(args.relation) + " " + str(output) + "\n")
        #obj_ids = find_wikidata(output, objects_ids, args.relation)
        obj_ids = find_wikidata(mtab_es, output, args.relation, args.linkingLLM, args.model_type, args.model)
        print("Object IDs (Wikidata Mapping):" + str(obj_ids) + "\n")
        if (args.explanation == "True"):
            query = create_explanation_prompt(query, output)
            print("\nPrompt to get confidence level in answer and explanation\n")
            print(query)
            print("\nSending prompt to model (" + args.model_type + ", " + args.model + ")...\n") 
            explanation = prompt_model(args.model_type, args.model, query) # prompt model with query
            print("Confidence level and explanation: " + explanation + "\n")
        if (args.dataset == "val" or args.dataset == "score"):
            fail = ""
            pred = Counter(obj_ids)
            true = Counter(row['ObjectEntitiesID'])
            pred_string = Counter(output)
            true_string = Counter(row['ObjectEntities'])
            if (pred == true):
                print("Predicted output " + str(output) + " is correct.\n")
                correctSamples += 1
            else:               
                if (pred_string == true_string):
                    print("Error in Wikidata Linking")
                    fail = "Wikidata Linking Failed."
                else:
                    print("Predicted output " + str(output) + " is incorrect. It should be " + str(row['ObjectEntities']) + ".\n")
                    fail = "LLM generated response different from Wikidata."
        result = {
            "SubjectEntityID": row["SubjectEntityID"],
            "SubjectEntity": row["SubjectEntity"],
            "Relation": row["Relation"],
            "ObjectEntities": output,
            "ObjectEntitiesID": obj_ids,
            "Explanation": explanation,
            "Fail": fail,
            "WikidataResponse": row['ObjectEntities']
        }
        results.append(result)    
        if (args.manual == "True"):
            end_flag, accepted = choiceWindow(row['SubjectEntity'], args.relation, output, obj_ids, row['ObjectEntities'], explanation)
            result["Accepted"] = accepted
            if end_flag:
                break  # Exit the loop if the user enters 'q'

    # 3 - Accuracy
    accuracy = correctSamples/numSamples * 100
    print("Accuracy: " + str(accuracy) + "%")
    # NOTE: since this is wikidata dataset it might be incomplete so answers from llm might be better
    # e.g., GPT: 76.9 for official languages - maybe prompts need improving?
    # e.g., LLAMA: 46.2 for official languages

    # 4 - Save results in Predictions File
    predictions_dir = 'predictions/{}-{}-{}-{}'.format(args.dataset, args.model, args.prompt, args.fewshot)
    if not os.path.exists(predictions_dir):
        os.makedirs(predictions_dir)
    save_df_to_jsonl(os.path.join(predictions_dir, '{}.jsonl'.format(args.relation)), results)

if __name__ == "__main__":
    main()
