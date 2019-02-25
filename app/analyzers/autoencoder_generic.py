from helpers.singletons import settings, es, logging
from analyzers.ml_models.dense_network import DenseNetwork
from helpers.outliers_error_based import OutliersErrorBased

import numpy as np


def es_to_numpy(es_json_hits, fields):
	'''
	Convert json to a numpy vector used in neural network
	'''	
	return np.array([np.float32(es_json_hits[k]) for k in fields])


def extract_model_settings(section_name):
	model_settings = dict()

	model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
	model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
	model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

	model_settings["layers"] = [int(k) for k in settings.config.get(section_name, "layers").split(',')]
	model_settings["epochs"] = settings.config.getint(section_name, "epochs")
	model_settings["fields"] = settings.config.get(section_name, "fields").split(',')
	model_settings["output_fields"] = settings.config.get(section_name, "output_fields").split(',')

	model_settings["ignore_history_window"] = settings.config.get(section_name, "ignore_history_window")
	model_settings["number_of_elements_displayed"] = settings.config.getint(section_name, "number_of_elements_displayed")	

	# Test the model
	model_settings["test_the_model"] = settings.config.getint(section_name, "test_the_model")
	model_settings["test_label"] = settings.config.get(section_name, "test_label")
	model_settings["number_of_points_plotted"] = settings.config.getint(section_name, "number_of_points_plotted")

	return model_settings

def perform_analysis():
	logging.logger.debug('\n' * 5)
	logging.logger.debug('#' * 16)
	logging.logger.debug('Autoencoder')
	logging.logger.debug('#' * 16)

	for section_name in settings.config.sections():
		if section_name != 'autoencoder':
			continue

		model_settings = extract_model_settings(section_name)

		# Don't use time range... (credicards don't have timestamp)
		if model_settings["ignore_history_window"] == '1':
			settings.search_range = None

		dataset = []
		output_fields = []

		for doc in es.scan(query_fields=model_settings["fields"] + model_settings["output_fields"]):
			_dataset = es_to_numpy(doc['_source'], model_settings["fields"])
			_output_fields = es_to_numpy(doc['_source'], model_settings["output_fields"])

			dataset.append(_dataset)
			output_fields.append(_output_fields)

		dataset = np.array(dataset)
		output_fields = np.array(output_fields)
			
		# Display information before starting autoencoder
		logging.logger.info('Dataset shape        %i - %i' % dataset.shape)
		logging.logger.info('Output fields shape  %i - %i' % output_fields.shape)
		logging.logger.info('Training the model')

		# Start algorithm
		autoencoder = DenseNetwork(model_settings["layers"])
		autoencoder.train_model(model_settings["epochs"], dataset, dataset)
		errors = autoencoder.measure_error(dataset)

		# Show results
		outliers = OutliersErrorBased(
								  errors, 
								  labels_title=model_settings["output_fields"],
								  labels=output_fields,
								  is_anormal=output_fields[:, 0])

		outliers.show_most_anormal(model_settings["number_of_elements_displayed"])

		# Benchmark
		if model_settings["test_the_model"]:
			outliers.plot_graph(model_settings["number_of_points_plotted"])
