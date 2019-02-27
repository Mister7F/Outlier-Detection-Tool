import numpy as np
import datetime
import math
import matplotlib.pyplot as plt
import gc

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

		across_aggregator_target = ['number_of_events', 'max_duration', 'min_duration', 'mean_duration', 'events_per_minute']
		
		if model_settings['target'] in across_aggregator_target:
			perform_analysis_across_aggregators(model_settings)
		else:
			perform_analysis_with_in_aggregator(model_settings)

		
def perform_analysis_across_aggregators(model_settings):
	
	lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

	total_documents = es.count_documents(lucene_query=lucene_query)
	logging.logger.info('Total documents: %i' % total_documents)

	aggregations = []
	aggregations_docs = []

	# Field analyzed across aggregators
	aggregations_target = []

	for aggregation, documents in es.time_based_scan(model_settings["aggregator"], model_settings["fields_value_to_correlate"], query_fields=[], lucene_query=lucene_query):
		aggregations.append(aggregation)

		agg_starts = []
		agg_durations = []

		for doc, start, duration in documents:
			# Keep only the first document for each aggregator
			if len(aggregations_docs) < len(aggregations):
				aggregations_docs.append(doc)

			agg_starts.append(start)
			agg_durations.append(duration)

		if not len(agg_starts):
			continue
	
		# Get method
		if model_settings['target'] == 'number_of_events':
			aggregations_target.append(len(agg_starts))

		elif model_settings['target'] == 'max_duration':
			aggregations_target.append(max(agg_durations))

		elif model_settings['target'] == 'min_duration':
			aggregations_target.append(min(agg_durations))

		elif model_settings['target'] == 'mean_duration':
			aggregations_target.append(np.array(agg_durations).mean())

		elif model_settings['target'] == 'events_per_minute':
			start_agg = min(agg_starts)
			end_agg = max(agg_starts)
			aggregator_time_range = ((end_agg-start_agg).total_seconds()/60) + 1
			n_events = len(agg_starts) - 1
			aggregations_target.append(n_events/aggregator_time_range)

			logging.logger.info('Aggregation %s has %i events in %s minutes' % (str(aggregation), len(agg_starts), aggregator_time_range))


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
		process_outlier(aggregations_docs[outlier], model_settings, aggregations_target[outlier])


def perform_analysis_with_in_aggregator(model_settings):
	lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

	total_documents = es.count_documents(lucene_query=lucene_query)
	logging.logger.info('Total documents: %i' % total_documents)

	aggregations = []
	all_targets = {}
	all_outliers = {}

	for aggregation, documents in es.time_based_scan(model_settings["aggregator"], model_settings["fields_value_to_correlate"], query_fields=[], lucene_query=lucene_query):
		logging.logger.info('Aggregation: %s' % aggregation)

		aggregations.append(aggregation)
		all_targets[aggregation] = []
		all_outliers[aggregation] = []

		read_next_batch = True
		i_batch = 0
		while read_next_batch:
			logging.logger.info('Batch %i' % i_batch)
			i_batch += 1

			batch_docs = []
			batch_starts = []
			batch_durations = []

			for i, (doc, start, duration) in enumerate(documents):	
				batch_docs.append(doc)	
				batch_starts.append(start)
				batch_durations.append(duration)

				if i == model_settings["batch_eval_size"]:
					break
			else:
				# It's the last batch
				read_next_batch = False

			batch_targets = get_time_targets(batch_starts, batch_durations, model_settings["target"])
			
			# Outliers detection
			agg_outliers = UnivariateOutlier(
				model_settings["trigger_method"],
				model_settings["trigger_sensitivity"]
			).detect_outliers(np.array(batch_targets))

			for index in agg_outliers:
				process_outlier(batch_docs[index], model_settings, batch_targets[index])
			
			all_targets[aggregation].extend(batch_targets)
			all_outliers[aggregation].extend([a + len(all_outliers[aggregation]) for a in agg_outliers])
			
			# Free the memory		
			del batch_docs
			del batch_starts
			del batch_durations
			del batch_targets
			# Garbage collector
			gc.collect()
	
	logging.logger.info('Number of aggregations: %i\t:\t' % len(aggregations))
	logging.logger.info('Number of elements: %i' % sum([len(all_targets[t]) for t in all_targets]))


	# Plot the histogram
	n_cols = min(3, len(all_targets))
	n_rows = math.ceil(len(all_targets) / n_cols)

	if n_rows > 20:
		logging.logger.info('To many aggregation to plot graph...')
		return

	plt.gcf().subplots_adjust(hspace=1)
	for i, aggregation in enumerate(all_targets):
		plt.subplot(n_rows, n_cols, i+1)

		xlabel = ' '.join(model_settings["target"].split('_'))
		xlabel = xlabel[0].upper() + xlabel[1:]

		data = np.array(all_targets[aggregation])
		out = all_outliers[aggregation]

		p_data = np.delete(data, out)
		p_out = data[out]
		if not p_out.size:
			plt.hist(p_data, bins=50, label=['Data'], color=['darkblue'], stacked=True)
		else:
			plt.hist([p_out, p_data], bins=50, label=['Outliers', 'Data'], color=['r', 'darkblue'], stacked=True)

		plt.title(model_settings["aggregator"] + ': ' + str(aggregation) + ' - ' + xlabel + ' - Histogram')
		plt.xlabel(xlabel)
		plt.ylabel('Count [log]')
		plt.yscale('log')
		plt.ylim(bottom=0.5)
		plt.legend()

	plt.show()


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
	model_settings["fields_value_to_correlate"] = settings.config.get(section_name, "fields_value_to_correlate").split(',')

	model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
	model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
	model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

	model_settings["target"] = settings.config.get(section_name, "target")
	model_settings["trigger_method"] = settings.config.get(section_name, "trigger_method")
	model_settings["trigger_sensitivity"] = settings.config.getfloat(section_name, "trigger_sensitivity")
	model_settings["batch_eval_size"] = settings.config.getint(section_name, "batch_eval_size")

	if model_settings["trigger_method"] not in ['mad', 'stdev', 'lof', 'lof_stdev']:
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

