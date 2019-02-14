# Debauche Stéphane
import numpy as np
from functools import reduce

from helpers.singletons import settings, es, logging
from helpers.outliers_error_based import OutliersErrorBased
from helpers.text_processing import onthot_encode

from analyzers.algorithms.k_means import k_means


def extract_model_settings(section_name):
	model_settings = dict()

	model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")
	model_settings["n_cluster"] = settings.config.getint(section_name, "n_cluster")
	model_settings["features"] = settings.config.get(section_name, "features").split(',')
	
	return model_settings

def perform_analysis():	
	for section_name in settings.config.sections():
		if section_name != 'clustering_str_k_mean':
			continue

		logging.logger.info('#################################')
		logging.logger.info('# Clustering string with K-Mean #')
		logging.logger.info('#################################')

		model_settings = extract_model_settings(section_name)

		lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])
		total_events = es.count_documents(lucene_query=lucene_query)

		logging.logger.info('Total events %i'%total_events)

		dataset = np.ndarray((total_events, len(model_settings["features"]))).astype(str)

		# Convert data to a 2d array of strings (lines: items, cols: features)
		for i, doc in enumerate(es.scan(
									lucene_query=lucene_query,
									query_fields=model_settings["features"]
								  )):
			doc_fields = es.extract_fields_from_document(doc)

			for j, field in enumerate(model_settings["features"]):
				dataset[i, j] = reduce((lambda x, y: x[y]), [doc_fields, *field.split('.')])

		# Onthot encode strings [features][item, dim]
		matrix = [onthot_encode(dataset[:, f]) for f in range(dataset.shape[1])]

		# Display vector size
		logging.logger.info('== Vectors size ==')
		for i, f in enumerate(model_settings["features"]):
			logging.logger.info('%s \t %s' % (f, str(matrix[i].shape)))
		logging.logger.info('==================')

		# [item, vector]
		matrix = np.array([
			np.concatenate([matrix[f][item] for f in range(2)])
			for item in range(total_events)
		])

		logging.logger.info('Dataset shape: ' + str(matrix.shape))

		# Clusterize
		points = k_means(matrix, n=model_settings["n_cluster"], max_iter=1000)

		# Show results
		logging.logger.info('Counts \t Values')
		logging.logger.info('====== \t ======')

		for i, cluster in enumerate(points):
			logging.logger.info('Cluster %i'%i)

			values, counts = np.unique(dataset[cluster, :], return_counts=True, axis=0)
			
			for v, c in zip(values, counts):
				logging.logger.info('-> %i \t %s' % (c, str(v)))

			


		











