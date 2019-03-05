import numpy as np
import datetime
import math
import matplotlib.pyplot as plt
import gc

import helpers
from helpers.outlier import Outlier
from helpers.singletons import settings, es, logging
from helpers.text_processing import class_to_id
from analyzers.algorithms.univariate_outliers import UnivariateOutlier


def perform_analysis():
	for section_name in settings.config.sections():
		if not section_name.startswith('duration_'):
			continue

		logging.logger.info('# Section ' + ' '.join(section_name[9:].split('_')) + ' #')

		model_settings = extract_model_settings(section_name)

		n_items = 0

		lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

		for doc, start, duration in es.scan_duration(
			model_settings['aggregator'],
			lucene_query,
			model_settings['start_end_field'],
			model_settings['start_value'],
			model_settings['end_value'],
			model_settings['fields_value_to_correlate']
		):
			n_items += 1

		logging.logger.info('N Items: %i' % n_items)

def get_target_extractor(target):
	allowed = [
		'start_timestamp', 'start_year', 'start_month', 'start_day', 'start_hour', 'start_minute', 
		'end_timestamp', 'end_year', 'end_month', 'end_day', 'end_hour', 'end_minute',
		'duration', 'log_duration'
	]

	if target not in allowed:
		raise Exception('Wrong time target')

	if target.startswith('start_'):
		target = target[6:]

		def ret(start, duration):
			value = start.__getattribute__(target)
			if type(value) is not int:
				value = value()
			return value

		return ret

	elif target.startswith('end_'):
		target = target[4:]

		def ret(start, duration):
			duration = datetime.timedelta(0, duration)
			value = (start + duration).__getattribute__(target)
			if type(value) is not int:
				value = value()
			return value

		return ret

	elif target == 'duration':
		def ret(start, duration):
			return duration

		return ret

	elif target == 'log_duration':
		def ret(start, duration):
			return np.log10(duration+1)

		return ret

	raise Exception('Wrong time target')


def extract_model_settings(section_name):
	model_settings = dict()

	model_settings["aggregator"] = settings.config.get(section_name, "aggregator")
	model_settings["fields_value_to_correlate"] = settings.config.get(section_name, "fields_value_to_correlate").split(',')

	model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")

	model_settings["start_end_field"] = settings.config.get(section_name, "start_end_field")
	model_settings["start_value"] = settings.config.get(section_name, "start_value")
	model_settings["end_value"] = settings.config.get(section_name, "end_value")

	model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
	model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
	model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

	model_settings["target"] = settings.config.get(section_name, "target")
	model_settings["trigger_method"] = settings.config.get(section_name, "trigger_method")
	model_settings["trigger_sensitivity"] = settings.config.getfloat(section_name, "trigger_sensitivity")
	model_settings["batch_eval_size"] = settings.config.getint(section_name, "batch_eval_size")

	try:
		model_settings["n_neighbors"] = settings.config.getint(section_name, "n_neighbors")
	except:
		model_settings["n_neighbors"] = 0

	if model_settings["trigger_method"] not in ['mad', 'stdev', 'lof', 'lof_stdev', 'isolation_forest']:
		raise 'Wrong trigger_method'

	try:
		model_settings["should_notify"] = settings.config.getboolean("notifier", "email_notifier") and settings.config.getboolean(section_name, "should_notify")
	except configparser.NoOptionError:
		model_settings["should_notify"] = False

	return model_settings


def process_outlier(doc, model_settings, target):    
    fields = es.extract_fields_from_document(doc)

    outlier_summary = model_settings["outlier_summary"].replace('<target>', str(target))
    outlier_summary = helpers.utils.replace_placeholder_fields_with_values(outlier_summary, fields)

    outlier = Outlier(type=model_settings["outlier_type"], reason=model_settings["outlier_reason"], summary=outlier_summary)

    es.process_outliers(doc=doc, outliers=[outlier], should_notify=model_settings["should_notify"])

    return outlier