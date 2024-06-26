
from file_io import read_lm_kbc_jsonl_to_df
import json
import argparse
from unidecode import unidecode

parser = argparse.ArgumentParser(
    description="Arguments of input"
)

# entity counter
parser.add_argument(
    "-c",
    "--counter",
    type=str,
    default="False",
    required=False,
    help="Entity counter"
)
parser.add_argument(
    "-t",
    "--theme",
    type=str,
    default="False",
    required=False,
    help="Theme"
)
args = parser.parse_args()

MAX = 30

data_df = read_lm_kbc_jsonl_to_df('StudyApp/study/{}_filtered.jsonl'.format(args.theme))

 # question
with open('StudyApp/question-prompts-study.json', 'r') as f:
    prompt_templates = json.load(f)
if (int(args.counter) <= MAX):
    row = data_df.iloc[int(args.counter) - 1]
    relation = row["Relation"]
    subject = row["SubjectEntity"]
    prompt_template = prompt_templates[relation]
    question = prompt_template.replace('{subject_entity}', subject)
    LLManswer = row["ObjectEntities"]
    WikidataAnswer = row["WikidataResponse"]
    if LLManswer == ['']:
        LLM_str = "Empty Answer "
    else:
        LLM_str = ""
        for i in LLManswer:
            LLM_str += " " + str(i) + ","
    if WikidataAnswer == ['']:
        Wikidata_str = "Empty Answer "
    else:
        Wikidata_str = ""
        for i in WikidataAnswer:
            Wikidata_str += " " + str(i) + ","
    
    list_row = str(row["SubjectEntityID"]) + "@" + unidecode(question) + "@" + unidecode(LLM_str[:-1]) + "@" + unidecode(Wikidata_str[:-1])
    print(list_row)
else:
    print("AC")
