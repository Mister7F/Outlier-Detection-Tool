import numpy as np

import helpers
from helpers.outlier import Outlier
from helpers.singletons import settings, es, logging
from helpers.outliers_error_based import OutliersErrorBased
from helpers.text_processing import class_to_id

def extract_model_settings(section_name):
	model_settings = dict()

	model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
	model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
	model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

	model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")
	model_settings["aggregator"] = settings.config.get(section_name, "aggregator")
	model_settings["item_identifier"] = settings.config.get(section_name, "item_identifier").split(',')

	model_settings["lower_duration_trigger"] = settings.config.getint(section_name, "lower_duration_trigger")
	model_settings["upper_duration_trigger"] = settings.config.getint(section_name, "upper_duration_trigger")
	model_settings["range_duration_trigger"] = settings.config.get(section_name, "range_duration_trigger")

	model_settings["range_duration_trigger"] = [int(i) for i in model_settings["range_duration_trigger"].split(',')]

	try:
		model_settings["should_notify"] = settings.config.getboolean("notifier", "email_notifier") and settings.config.getboolean(section_name, "should_notify")
	except configparser.NoOptionError:
		model_settings["should_notify"] = False

	return model_settings

def perform_analysis():	
	for section_name in settings.config.sections():
		if not section_name.startswith('anormal_duration'):
			continue

		logging.logger.info('####################')
		logging.logger.info('# Anormal duration #')
		logging.logger.info('####################')

		model_settings = extract_model_settings(section_name)

		lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

		n_aggregations = 0
		n_items = 0
		total_duration = 0
		zero_duration = 0

		for aggregation, documents in es.time_based_scan(model_settings["aggregator"], model_settings["item_identifier"], query_fields=[], lucene_query=lucene_query):
			n_aggregations += 1
			for doc, start, duration in documents:
				n_items += 1
				total_duration += duration

				if not duration:
					zero_duration += 1

				if duration <= model_settings["lower_duration_trigger"]:
					process_outlier(doc, model_settings, duration)

				elif duration >= model_settings["upper_duration_trigger"] >= 0:
					process_outlier(doc, model_settings, duration)
				
				elif model_settings["range_duration_trigger"][0] < duration < model_settings["range_duration_trigger"][1]:
					process_outlier(doc, model_settings, duration)

		logging.logger.info('Number of aggregations: %i'%n_aggregations)
		logging.logger.info('Number of elements: %i'%n_items)
		logging.logger.info('Average duration: %f'%(total_duration/n_items))	
		logging.logger.info('Zero duration: %i'%zero_duration)


def process_outlier(doc, model_settings, duration):
    
    fields = es.extract_fields_from_document(doc)

    outlier_summary = model_settings["outlier_summary"].replace('<duration>', str(duration))
    outlier_summary = helpers.utils.replace_placeholder_fields_with_values(outlier_summary, fields)


    outlier = Outlier(type=model_settings["outlier_type"], reason=model_settings["outlier_reason"], summary=outlier_summary)

    es.process_outliers(doc=doc, outliers=[outlier], should_notify=model_settings["should_notify"])

    return outlier