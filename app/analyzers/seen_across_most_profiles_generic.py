import numpy as np
from functools import reduce
import re

from helpers.singletons import settings, es, logging

'''
How does it work ?

Take two features
	- One as input, this feature will be onehot encoded
	- One as output, this feature is text
	  The text will be splitted into words and words
	  will be vectorized
'''

def extract_model_settings(section_name):
	model_settings = dict()

	model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
	model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
	model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

	model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")
	model_settings["aggregator"] = settings.config.get(section_name, "aggregator")
	model_settings["target"] = settings.config.get(section_name, "target")
	model_settings["tokenizer_split_path"] = settings.config.get(section_name, "tokenizer_split_path").split(',')
	model_settings["tokenizer_max_dic_size"] = settings.config.getint(section_name, "tokenizer_max_dic_size")
	model_settings["path_regex"] = settings.config.get(section_name, "path_regex")
	model_settings["path_truncation"] = settings.config.getint(section_name, "path_truncation")	

	model_settings["layers"] = [int(i) for i in settings.config.get(section_name, "layers").split(',')]
	model_settings["epochs"] = settings.config.getint(section_name, "epochs")
	
	return model_settings

def perform_analysis():	
	for section_name in settings.config.sections():
		if section_name != 'sentence_prediction':
			continue

		logging.logger.info('#######################')
		logging.logger.info('# Sentence prediction #')
		logging.logger.info('#######################')

		model_settings = extract_model_settings(section_name)

		lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])
		total_events = es.count_documents(lucene_query=lucene_query)

		logging.logger.info('Total events %i'%total_events)

		fields = [model_settings["aggregator"], model_settings["target"]]

		dataset = np.array([
			es.get_fields_by_path(doc, fields)
			for doc in es.scan(lucene_query=lucene_query, query_fields=fields)
		]).astype('object')



		# Change each process by an id
		x_data, process_dic = class_to_id(dataset[:, 0], return_dic=True)

		# Extact path from command line
		for i in range(dataset.shape[0]):
			dataset[i, 1] = dataset[i, 1].lstrip()
			groups = re.findall(model_settings["path_regex"], dataset[i, 1])
			if len(groups):
				dataset[i, 1] = groups[0][0]
			else:
				dataset[i, 1] = 'no_regex_match - ' + dataset[i, 1]

		