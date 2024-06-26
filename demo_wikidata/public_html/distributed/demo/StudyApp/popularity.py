import requests
import argparse
from requests import utils
import os
from sparql import WikiDataQueryResults
from bs4 import BeautifulSoup
import json


from file_io import read_lm_kbc_jsonl_to_df, save_df_to_jsonl
from sparql import WikiDataQueryResults

# python popularity.py -r CountryHasOfficialLanguage -d val
# 1. search items in wikipedia (for a given category) given info in wikidata - year:2023
# 2. get # accesses for items
# 3. get # edits of items
# 4. select top searched items and that change more

def get_edits(search_field):
	print(search_field)
	endpoint = f"https://en.wikipedia.org/wiki/{search_field}?action=info"
	try:
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
		response = requests.get(endpoint, headers=headers)
		soup = BeautifulSoup(response.content, 'html.parser')
		nr_edits_tr = soup.find("tr", {"id": "mw-pageinfo-edits"})
		nr_edits = nr_edits_tr.get_text()
		nr_edits = nr_edits.replace("Total number of edits", "")
		nr_edits = nr_edits.replace(",", '')
		nr_edits = int(nr_edits)
		return nr_edits
	except Exception as e:
		print(f"An error occurred: {e}")


def get_views(search_field):
	num_views = 0
	endpoint = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{search_field}/monthly/2023010100/2023123100"
	try:
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
		response = requests.get(endpoint, headers=headers)
		data = response.json()
		for d in data['items']:
			num_views += int(d['views'])
		return num_views
	except Exception as e:
		print(f"An error occurred: {e}")

def get_wikipedia_url_from_wikidata_id(wikidata_id, lang='en', debug=False):
    url = (
        'https://www.wikidata.org/w/api.php'
        '?action=wbgetentities'
        '&props=sitelinks/urls'
        f'&ids={wikidata_id}'
        '&format=json')
    json_response = requests.get(url).json()
    if debug: print(wikidata_id, url, json_response) 

    entities = json_response.get('entities')    
    if entities:
        entity = entities.get(wikidata_id)
        if entity:
            sitelinks = entity.get('sitelinks')
            if sitelinks:
                if lang:
                    # filter only the specified language
                    sitelink = sitelinks.get(f'{lang}wiki')
                    if sitelink:
                        wiki_url = sitelink.get('url')
                        if wiki_url:
                            return requests.utils.unquote(wiki_url)
                else:
                    # return all of the urls
                    wiki_urls = {}
                    for key, sitelink in sitelinks.items():
                        wiki_url = sitelink.get('url')
                        if wiki_url:
                            wiki_urls[key] = requests.utils.unquote(wiki_url)
                    return wiki_urls
    return None


parser = argparse.ArgumentParser(
    description="Arguments of input"
)

# relation between the subject entity and the objects
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
)

args = parser.parse_args()

data_df = read_lm_kbc_jsonl_to_df('data/{}.jsonl'.format(args.dataset))
data_df = data_df[data_df['Relation'] == args.relation].copy()

def save_file(prop):
	dict_items = {}
	results = []
	for idx, row in data_df[:].iterrows():
		id_item = row["SubjectEntityID"]
		wikipedia_url = get_wikipedia_url_from_wikidata_id(id_item)
		if wikipedia_url != None:
			search_field = wikipedia_url.replace("https://en.wikipedia.org/wiki/", "")
			if (prop == "Views"):
				prop_arr = get_views(search_field)
			elif (prop == "Edits"):
				prop_arr = get_edits(search_field)

			dict_items[search_field] = prop_arr
			result = {
				"SubjectEntityID": row["SubjectEntityID"],
				"SubjectEntity": row["SubjectEntity"],
				"ObjectEntities": row["ObjectEntities"],
				"ObjectEntitiesID": row["ObjectEntitiesID"],
				"Relation": row["Relation"],
				prop : prop_arr
			}

			results.append(result)

	# bubble sort
	n = len(results)
	for i in range(n-1):
		swapped = False
		for j in range(0, n-i-1):
			arr_1 = results[j][prop]
			arr_2 = results[j+1][prop]
			if arr_1 == None:
				arr_1 = 0
			if arr_2 == None:
				arr_2 = 0
			if arr_1 < arr_2:
				swapped = True
				results[j], results[j+1] = results[j+1], results[j]

	data_dir = 'data_' + prop
	if not os.path.exists(data_dir):
		os.makedirs(data_dir)
	save_df_to_jsonl(os.path.join(data_dir, '{}.jsonl'.format(args.relation)), results)

save_file("Views")
save_file("Edits")