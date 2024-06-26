import requests
from time import time
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from prompt import create_choose_option_prompt
from models import prompt_model

class MTabES(object):
    def __init__(self):
        self.URL = "http://mtab.kgraph.jp/api/v1/search"
        self.session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def get(self, query_value, limit=20, mode="a", lang="en", expensive=0, info=0):
        query_args = {
            "q": query_value,
            "limit": limit,
            "m": mode,
            "lang": lang,
            "info": info,
            "expensive": expensive
        }
        start = time()
        responds = []
        if not query_value:
            return [], time() - start
        try:
            # tmp_responds = requests.get(self.URL, params=query_args)
            tmp_responds = self.session.get(self.URL, params=query_args)
            if tmp_responds.status_code == 200:
                tmp_responds = tmp_responds.json()
                if tmp_responds.get("hits"):
                    if info:
                        responds = [[r["id"], r["score"], r["label"], r["des"]] for r in tmp_responds["hits"]]
                    else:
                        responds = [[r["id"], r["score"]] for r in tmp_responds["hits"]]
        except Exception as message:
            print(f"\n{message}\n{str(query_args)}")
        run_time = time() - start
        return responds, run_time

# find LLM responses in wikidata - sparql query
def find_wikidata(mtab_es, items, relation, linkLLM, model_type, model):
    if relation == "SeriesHasNumberOfEpisodes" or relation == "PersonHasNumberOfChildren": # in case it is a number of things this will be empty
        return items
    ids = []
    for item in items:
        equal_values = 0
        modes = ["a"]  # "a", "b", "f"
        lang_opts = ["en"]  # "en", "all"
        expensive_opts = [0]  # 0, 1
        info = 1 # get entity information
        for mode in modes:
            for lang in lang_opts:
                for expensive in expensive_opts:
                    responds, run_time = mtab_es.get(item, limit=20, mode=mode, lang=lang, expensive=expensive, info=info)
                    str_ties = ""
                    list_ties = []
                    max_score = 0
                    if (linkLLM == "True"):
                        for i, (r, s, l, d) in enumerate(responds[:3]):
                            max_score = max(max_score, s)
                            if (abs(s-max_score) < 0.0001):
                                str_ties += str(i) + ". " + l + ":" + " " + d + "\n"
                                list_ties.append(r)
                            print(f"{i + 1:2}. {s:.4f} - {r}[{l}] - {d}")
                            print()
                        if (len(list_ties) > 1):
                            full_prompt = create_choose_option_prompt(str_ties, relation)
                            print(full_prompt)
                            response = prompt_model(model_type, model, full_prompt)
                            idx = int(response[0])
                            print(idx)
                            ids.append(list_ties[idx])
                        else:
                            ids.append(list_ties[0])
                    else:
                        for i, (r, s, l, d) in enumerate(responds[:1]):
                            print(f"{i + 1:2}. {s:.4f} - {r}[{l}] - {d}")
                            print()
                            ids.append(r)

    if len(ids) == 0:
        ids = ['']
    return ids
 
