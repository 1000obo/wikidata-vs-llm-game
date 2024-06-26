from file_io import read_lm_kbc_jsonl_to_df, save_df_to_jsonl
import os
import math

relation = "BandHasMember"
max_entities = 10
views_df = read_lm_kbc_jsonl_to_df('data_Views/' + relation + '.jsonl')
edits_df = read_lm_kbc_jsonl_to_df('data_Edits/' + relation + '.jsonl')

def compute_max(df, string):
	max_val = 0
	for idx, row in df[:].iterrows():
		if not math.isnan(row[string]):
			val = int(row[string])
			if val > max_val:
				max_val = val
	return max_val

def results_percentage():
	results = []
	for idx_v, row_v in views_df[:].iterrows():
		if not math.isnan(row_v["Views"]):
			val_v = int(row_v['Views'])/max_views
			for idx_e, row_e in edits_df[:].iterrows():
				if row_v["SubjectEntityID"] == row_e["SubjectEntityID"]:
					if not math.isnan(row_e["Edits"]):
						val_e = int(row_e['Edits'])/max_edits
						total_val = (val_v + val_e)/2 # criterias have the same importance
						result = {
							"SubjectEntityID": row_e["SubjectEntityID"],
							"SubjectEntity": row_e["SubjectEntity"],
							"ObjectEntities": row_e["ObjectEntities"],
							"ObjectEntitiesID": row_e["ObjectEntitiesID"],
							"Relation": row_e["Relation"],
							"Score" : total_val
						}
						results.append(result)
						break
	return results

def save_file(results):
	# bubble sort
	n = len(results)
	for i in range(n-1):
		swapped = False
		for j in range(0, n-i-1):
			arr_1 = results[j]["Score"]
			arr_2 = results[j+1]["Score"]
			if arr_1 == None:
				arr_1 = 0
			if arr_2 == None:
				arr_2 = 0
			if arr_1 < arr_2:
				swapped = True
				results[j], results[j+1] = results[j+1], results[j]

	data_dir = 'data_Score'
	if not os.path.exists(data_dir):
		os.makedirs(data_dir)
	save_df_to_jsonl(os.path.join(data_dir, '{}.jsonl'.format(relation)), results[0:max_entities])

max_views = compute_max(views_df, "Views")
max_edits = compute_max(edits_df, "Edits")
results = results_percentage()
save_file(results)
