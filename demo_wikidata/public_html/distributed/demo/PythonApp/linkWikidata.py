import requests
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sparql import WikiDataQueryResults

# find LLM responses in wikidata - sparql query
def find_wikidata(items, relation):
	ids = [] # Question: what if I can't find any? for drum pad - todo: Too slow + other entities show up (maybe count and order but it's already so slow) + similarity search
	for item in items:
		if item != '' and item != "''":
			url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={item}&language=en&format=json"
			data = requests.get(url).json()
			if len(data['search']) > 0:
				most_sim = 0
				most_sim_val = 0
				# filter this according to relation if more than one result found - TODO: languages this does not work well
				if (relation != "CountryHasOfficialLanguage"):
					for idx, i in enumerate(data['search']):
						if ("description" in i['display']):
							sim_val = pairwise_sim(relation, i['display']['description']['value'])
							if (sim_val > most_sim_val):
								most_sim = idx
								most_sim_val = sim_val					
				ids.append(data['search'][most_sim]['id'])
			else:
				ids.append("Not Found in Wikidata")
			'''query = """
			SELECT ?object
			WHERE {
			  ?subject wdt:%s ?object.
			  {
			    ?object rdfs:label ?label.
			    FILTER (LANG(?label) = "en" && CONTAINS(LCASE(?label), LCASE('%s')))
			  }
			  UNION
			  {
			    ?object skos:altLabel ?altLabel.
			    FILTER (LANG(?altLabel) = "en" && CONTAINS(LCASE(?altLabel), LCASE('%s')))
			  }
			  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }
			}
			LIMIT 10
			""" % (relation, item, item)
			data_extracter = WikiDataQueryResults(query)
			df = data_extracter.load_as_dataframe()
			if not df.head().empty:
				id = 'Q' + re.search(r'/Q(\d+)', df.loc[0, 'object']).group(1)
				ids.append(id)'''
	if len(ids) == 0:
		ids = ['']
	return ids


# similarity of relation with the entity found - e.g., portuguese should be the language and not the people the relation CountryHasOfficialLanguage
def pairwise_sim(relation, text):
	relation = ' '.join(re.findall('[A-Z][^A-Z]*', relation))
	tfidf = TfidfVectorizer().fit_transform([relation, text])
	return ((tfidf * tfidf.T).A)[0,1]

'''
url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={item}&language=en&format=json"
			data = requests.get(url).json()
			if len(data['search']) > 0:
				most_sim = 0
				most_sim_val = 0
				# filter this according to relation if more than one result found - TODO: languages this does not work well
				if (relation != "CountryHasOfficialLanguage"):
					for idx, i in enumerate(data['search']):
						if ("description" in i['display']):
							sim_val = pairwise_sim(relation, i['display']['description']['value'])
							if (sim_val > most_sim_val):
								most_sim = idx
								most_sim_val = sim_val					
				ids.append(data['search'][most_sim]['id'])
			else:
				ids.append("Not Found in Wikidata")
'''