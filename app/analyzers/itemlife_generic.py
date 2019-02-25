import numpy as np
import datetime

import helpers
from helpers.outlier import Outlier
from helpers.singletons import settings, es, logging
from helpers.outliers_error_based import OutliersErrorBased
from helpers.text_processing import class_to_id
from analyzers.algorithms.univariate_outliers import UnivariateOutlier


def perform_analysis():	
	for section_name in settings.config.sections():
		if not section_name.startswith('itemlife_'):
			continue

		logging.logger.info('# Section ' + ' '.join(section_name[9:].split('_')) + ' #')

		model_settings = extract_model_settings(section_name)

		across_aggregator_target = ['number_of_events', 'max_duration', 'min_duration', 'mean_duration']
		
		if model_settings['target'] in across_aggregator_target:
			perform_analysis_across_aggregators(model_settings)
		else:
			perform_analysis_with_in_aggregator(model_settings)

		
def perform_analysis_across_aggregators(model_settings):
	
	lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

	total_documents = es.count_documents(lucene_query=lucene_query)
	logging.logger.info('Total documents: %i' % total_documents)

	aggregations = []
	aggregations_docs = {}
	aggregations_starts = {}
	aggregations_durations = {}

	for aggregation, documents in es.time_based_scan(model_settings["aggregator"], model_settings["item_identifiers"], query_fields=[], lucene_query=lucene_query):
		aggregations.append(aggregation)
		aggregations_docs[aggregation] = []
		aggregations_starts[aggregation] = []
		aggregations_durations[aggregation] = []

		for doc, start, duration in documents:	
			aggregations_docs[aggregation].append(doc)			
			aggregations_starts[aggregation].append(start)
			aggregations_durations[aggregation].append(duration)

	aggregations_target = []

	# Get method
	if model_settings['target'] == 'number_of_events':
		for agg in aggregations:
			aggregations_target.append(len(aggregations_docs[agg]))

	elif model_settings['target'] == 'max_duration':
		for agg in aggregations:
			aggregations_target.append(max(aggregations_durations[agg]))

	elif model_settings['target'] == 'min_duration':
		for agg in aggregations:
			aggregations_target.append(min(aggregations_durations[agg]))

	elif model_settings['target'] == 'mean_duration':
		for agg in aggregations:
			aggregations_durations[agg] = np.array(aggregations_durations[agg])
			aggregations_target.append(aggregations_durations[agg].mean())

	aggregations_target = np.array(aggregations_target)

	# Outliers detection
	outliers = UnivariateOutlier(
		model_settings["trigger_method"],
		model_settings["trigger_sensitivity"]
	).detect_outliers(aggregations_target)

	tmp = np.ones(aggregations_target.shape); tmp[outliers] = 0
	histogram_outliers(aggregations_target[tmp==1], aggregations_target[tmp==0], xlabel=model_settings["target"], bins=48)

	for outlier in outliers:
		agg = aggregations[outlier]
		# Process only the first doc of the aggregation,
		# this document represent the aggregation...
		process_outlier(aggregations_docs[agg][0], model_settings, aggregations_target[outlier])



def perform_analysis_with_in_aggregator(model_settings):
	lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

	total_documents = es.count_documents(lucene_query=lucene_query)
	logging.logger.info('Total documents: %i' % total_documents)

	aggregations = []
	all_targets = []
	outliers = []

	for aggregation, documents in es.time_based_scan(model_settings["aggregator"], model_settings["item_identifiers"], query_fields=[], lucene_query=lucene_query):
		aggregations.append(aggregation)

		agg_docs = []
		agg_starts = []
		agg_durations = []

		for doc, start, duration in documents:	
			agg_docs.append(doc)			
			agg_starts.append(start)
			agg_durations.append(duration)

		agg_targets = get_time_targets(agg_starts, agg_durations, model_settings["target"])
		
		if len(agg_targets) < 2:
			logging.logger.warning('This aggregation is too small to detect outliers... [%s]' % aggregation)
			continue

		# Outliers detection
		agg_outliers = UnivariateOutlier(
						model_settings["trigger_method"],
						model_settings["trigger_sensitivity"]
					).detect_outliers(np.array(agg_targets))

		for index in agg_outliers:
			process_outlier(agg_docs[index], model_settings, agg_targets[index])

		outliers.extend(agg_outliers + len(all_targets))
		all_targets.extend(agg_targets)

	all_targets = np.array(all_targets)
	
	logging.logger.info('Number of aggregations: %i\t:\t' % len(aggregations) + ' - '.join(aggregations))
	logging.logger.info('Number of elements: %i' % len(all_targets))
	logging.logger.info('Average target: %f' % all_targets.mean())
	logging.logger.info('Max target: %i' % all_targets.max())
	logging.logger.info('Min target: %i' % all_targets.min())

	tmp = np.ones(all_targets.shape); tmp[outliers] = 0
	histogram_outliers(all_targets[tmp==1], all_targets[tmp==0], xlabel=model_settings["target"], bins=48)


def get_time_targets(starts, durations, target):
	allowed = [
		'start_timestamp', 'start_year', 'start_month', 'start_day', 'start_hour', 'start_minute', 
		'end_timestamp', 'end_year', 'end_month', 'end_day', 'end_hour', 'end_minute',
		'duration'
	]

	if target not in allowed:
		raise 'Wrong time target'

	if target.startswith('start_'):
		target = target[6:]

		values = []
		for start in starts:
			value = start.__getattribute__(target)
			if type(value) is not int:
				value = value()
			values.append(value)

		return values

	elif target.startswith('end_'):
		target = target[4:]

		values = []
		for start, duration in zip(starts, durations):
			duration = datetime.timedelta(0, duration)
			value = (start + duration).__getattribute__(target)
			if type(value) is not int:
				value = value()
			values.append(value)

		return values

	elif target == 'duration':
		return durations

	raise 'Wrong time target'


def histogram_outliers(data, outliers=[], xlabel='Value', bins=200):
    xlabel = ' '.join(xlabel.split('_'))
    xlabel = xlabel[0].upper() + xlabel[1:]

    import matplotlib.pyplot as plt
    plt.hist([outliers, data], bins=bins, label=['Outliers', 'Data'], color=['r', 'darkblue'], stacked=True)
    plt.title(xlabel + ' - Histogram')
    plt.xlabel(xlabel)
    plt.ylabel('Count [log]')
    plt.yscale('log')
    plt.ylim(bottom=0.5)
    plt.legend()
    plt.show()


def extract_model_settings(section_name):
	model_settings = dict()

	model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")
	model_settings["aggregator"] = settings.config.get(section_name, "aggregator")
	model_settings["item_identifiers"] = settings.config.get(section_name, "item_identifiers").split(',')

	model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
	model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
	model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

	model_settings["target"] = settings.config.get(section_name, "target")
	model_settings["trigger_method"] = settings.config.get(section_name, "trigger_method")
	model_settings["trigger_sensitivity"] = settings.config.getint(section_name, "trigger_sensitivity")

	if model_settings["trigger_method"] not in ['mad', 'stdev', 'lof']:
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

