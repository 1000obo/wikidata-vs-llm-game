from wikidb.core.db_wd import DBWikidata
import wikidb.config as cf
import time
from thefuzz import fuzz

import requests
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sparql import WikiDataQueryResults

relation_dict = {
    "BandHasMember": "Q5", # TODO: too long but match is right
    "CityLocatedAtRiver": "Q4022", # yes
    "CompanyHasParentOrganisation": "Q891723", # yes - for analysis: why does it name companies?
    "CompoundHasParts": "Q11344", # yes
    "CountryBordersCountry": "Q6256", # yes - for analysis: maritime borders also count...
    "CountryHasOfficialLanguage": "Q34770", # yes
    "CountryHasStates": "Q34876", # TODO
    "FootballerPlaysPosition": "Q4611891", # yes - but they are linking to rugby.. this is soccer! maybe compare with limiting choices
    "PersonCauseOfDeath": "Q1931388", # ?
    "PersonHasAutobiography": "Q47461344", #TODOODOD
    "PersonHasEmployer": "Q4830453", # TOODODDO
    "PersonHasNoblePrize": "Q7191", # yes
    "PersonHasNumberOfChildren": "", # no need
    "PersonHasPlaceOfDeath": "", # ?
    "PersonHasProfession": "Q28640", # not sure
    "PersonHasSpouse": "Q5", # ?
    "PersonPlaysInstrument": "Q34379", # TOODODO
    "PersonSpeaksLanguage": "Q34770", # yes
    "RiverBasinsCountry": "Q6256", # yes
    "SeriesHasNumberOfEpisodes": "", # no need
    "StateBordersState": "Q34876" # TODO
}

# list wikidata objects that match relation
def list_wikidata_relation(relation):
	db = DBWikidata()
	ids = []
	if relation_dict[relation] != "":
		if relation == "PersonHasNoblePrize" or relation == "PersonPlaysInstrument":
			ids = find_wikidata_items_haswbstatements(db, [[cf.ATTR_OPTS.AND, "P279", relation_dict[relation]]])
		elif relation == "BandHasMember":
			ids = find_wikidata_items_haswbstatements(db,
				[
					[cf.ATTR_OPTS.AND, "P31", "Q5"], #human
					[cf.ATTR_OPTS.OR, "P106", "Q177220"], #singer
					[cf.ATTR_OPTS.OR, "P106", "Q855091"], #guitarist
					[cf.ATTR_OPTS.OR, "P106", "Q386854"], #drummer
				]
			)
		elif relation == "PersonCauseOfDeath":
			ids = find_wikidata_items_haswbstatements(db,
				[
					[cf.ATTR_OPTS.OR, "", "Q121551339"], #traffic collision
					[cf.ATTR_OPTS.OR, "", "Q1931388"], #cause of death

				]
			)
		elif relation == "PersonHasAutobiography":
			ids = find_wikidata_items_haswbstatements(db,
				[
					[cf.ATTR_OPTS.AND, "P31", "Q47461344"], #written work
					[cf.ATTR_OPTS.OR, "P31", "Q7725634"], #literary work

				]
			)
		else:
			ids = find_wikidata_items_haswbstatements(db, [[cf.ATTR_OPTS.AND, "P31", relation_dict[relation]]])
	return ids



def clean_string(string, relation):
		if relation == "CityLocatedAtRiver":
			return string.replace("River", "")
		else:
			return string 

# find LLM responses in wikidata - sparql query
def find_wikidata(items, list_wikidata, relation):
	if len(list_wikidata) == 0: # in case it is a number of things this will be empty
		return items
	db = DBWikidata()
	ids = []
	for item in items:
		item = clean_string(item, relation)
		similarity_score = 0
		saved_id = ''
		for i in list_wikidata:
			label = db.get_label(i)
			label = clean_string(label, relation)
			temp_sim_score = fuzz.ratio(label, item)
			aliases = db.get_aliases(i, 'en')
			if aliases:
				for alias in aliases:
					alias = clean_string(alias, relation)
					alias_sim_score = fuzz.ratio(alias, item)
					temp_sim_score = max(temp_sim_score, alias_sim_score)
			if temp_sim_score > similarity_score:
				similarity_score = temp_sim_score
				saved_id = i
		ids.append(saved_id)
		print(item)
		print(db.get_label(saved_id))
	if len(ids) == 0:
		ids = ['']
	return ids

def find_wikidata_items_haswbstatements(db, params, print_top=3, get_qid=True):
    start = time.time()
    wd_ids = db.get_haswbstatements(params, get_qid=get_qid)
    end = time.time() - start
    print("Query:")
    for logic, prop, qid in params:
      if prop is None:
          prop_label = ""
      else:
          prop_label = f" - {prop}[{db.get_label(prop)}]"

      qid_label = db.get_label(qid)
      print(f"{logic}{prop_label}- {qid}[{qid_label}]")

    print(f"Answers: Found {len(wd_ids):,} items in {end:.5f}s")
    for i, wd_id in enumerate(wd_ids[:print_top]):
    	print(f"{i+1}. {wd_id} - {db.get_label(wd_id)}")
    print(f"{4}. ...")
    print()
    return wd_ids


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

'''OTHER TRIES
SELECT ?object
WHERE {
  ?subject wdt:P1303 ?object.
  ?object rdfs:label ?objectLabel.
  FILTER (LANG(?objectLabel) = "en" && LCASE(?objectLabel) = 'piano')
}
LIMIT 10


			  ?object wdt:P279* wd:Q34379.


query = """
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



	
	# Question: what if I can't find any? for drum pad - todo: Too slow + other entities show up (maybe count and order but it's already so slow) + similarity search
	for item in items:
		if item != '' and item != "''":
			query = """
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
				ids.append(id)
	if len(ids) == 0:
		ids = ['']
'''


