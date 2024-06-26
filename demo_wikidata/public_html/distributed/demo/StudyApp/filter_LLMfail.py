from file_io import read_lm_kbc_jsonl_to_df, save_df_to_jsonl
import os
import math

theme = "popCulture"
df = read_lm_kbc_jsonl_to_df('study/' + theme + '.jsonl')

def filter_file():
	results = []
	for idx, row in df[:].iterrows():
		if row["Fail"] == "LLM generated response different from Wikidata.":				
			result = {
				"SubjectEntityID": row["SubjectEntityID"],
				"SubjectEntity": row["SubjectEntity"],
				"ObjectEntities": row["ObjectEntities"],
				"ObjectEntitiesID": row["ObjectEntitiesID"],
				"Relation": row["Relation"],
				"WikidataResponse" : row["WikidataResponse"]
			}
			results.append(result)
	return results

def save_file(results):
	data_dir = 'study'
	if not os.path.exists(data_dir):
		os.makedirs(data_dir)
	save_df_to_jsonl(os.path.join(data_dir, '{}_filtered.jsonl'.format(theme)), results)

results = filter_file()
save_file(results)
