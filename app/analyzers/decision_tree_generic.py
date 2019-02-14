# Debauche Stéphane
import numpy as np

from helpers.singletons import settings, es, logging
from analyzers.algorithms.decision_tree import Tree

def extract_model_settings(section_name):
	model_settings = dict()

	model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")
	model_settings["aggregators"] = settings.config.get(section_name, "aggregators").split(',')
	model_settings["target"] = settings.config.get(section_name, "target")
	model_settings["max_depth"] = settings.config.getint(section_name, "max_depth")
	model_settings["feature_type"] = settings.config.get(section_name, "feature_type").split(',')
	
	return model_settings
	
def perform_analysis():	
	for section_name in settings.config.sections():
		if section_name != 'decision_tree':
			continue

		logging.logger.info('#################')
		logging.logger.info('# DECISION TREE #')
		logging.logger.info('#################')

		model_settings = extract_model_settings(section_name)

		fields = model_settings["aggregators"] + [model_settings["target"]]

		lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])
		total_events = es.count_documents(lucene_query=lucene_query)

		logging.logger.info('Total events: %i' % total_events)

		dataset = np.array([
			[es.get_field_by_path(doc, agg) for agg in fields]
			for doc in es.scan(lucene_query=lucene_query, query_fields=fields)
		]).astype('object')

		for i, f in enumerate(model_settings["feature_type"]):
			if f == 'enum':
				dataset[:, i] = dataset[:, i].astype('str')
			else:
				dataset[:, i] = dataset[:, i].astype('float')

		logging.logger.info('Start to build the tree...')

		tree = Tree(dataset, model_settings["feature_type"], model_settings["max_depth"])

		logging.logger.info('This tree want to classify %s' % model_settings["target"])
		logging.logger.info('Features used: ' + str(model_settings["aggregators"]))
		logging.logger.info('\n' + '=' * 30 + '\n\n' + str(tree) + '\n\n' + '=' * 30)



