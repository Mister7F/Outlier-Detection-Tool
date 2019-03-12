import numpy as np
import datetime
import math
import matplotlib.pyplot as plt
import gc
import json

import helpers
from helpers.outlier import Outlier
from helpers.singletons import settings, es, logging
from helpers.text_processing import class_to_id
from analyzers.algorithms.univariate_outliers import UnivariateOutlier
from helpers.ploter import *


def perform_analysis():
    for section_name in settings.config.sections():
        if not section_name.startswith('duration_'):
            continue

        logging.logger.info(
            '# Section ' + ' '.join(section_name[9:].split('_')) + ' #')

        model_settings = extract_model_settings(section_name)

        across_aggregator_target = [
            'number_of_events',
            'max_duration',
            'min_duration',
            'mean_duration',
            'events_per_minute'
        ]

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

    extract_target = get_target_extractor(model_settings["target"])

    for aggregation, documents in es.scan_duration(
            model_settings['aggregator'],
            es.filter_by_query_string(model_settings["es_query_filter"]),
            model_settings['start_condition'],
            model_settings['end_condition'],
            model_settings['fields_value_to_correlate']
    ):
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

        aggregations_target.append(extract_target(agg_starts, agg_durations))

    aggregations_target = np.array(aggregations_target)

    # Outliers detection
    outliers = UnivariateOutlier(
        model_settings["trigger_method"],
        model_settings["trigger_sensitivity"],
        model_settings["n_neighbors"]
    ).detect_outliers(aggregations_target)

    if model_settings["plot_graph"]:
        histogram_outliers(
            aggregations_target,
            outliers,
            xlabel=model_settings["target"],
            bins=48,
            yscale='log'
        )

    for outlier in outliers:
        agg = aggregations[outlier]
        # Process only the first doc of the aggregation,
        # this document represent the aggregation...
        process_outlier(
            aggregations_docs[outlier],
            model_settings,
            aggregations_target[outlier]
        )


def perform_analysis_with_in_aggregator(model_settings):
    lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

    total_documents = es.count_documents(lucene_query=lucene_query)
    logging.logger.info('Total documents: %i' % total_documents)

    aggregations = []
    all_targets = {}
    all_outliers = {}

    extract_target = get_target_extractor(model_settings["target"])

    for aggregation, documents in es.scan_duration(
            model_settings['aggregator'],
            es.filter_by_query_string(model_settings["es_query_filter"]),
            model_settings['start_condition'],
            model_settings['end_condition'],
            model_settings['fields_value_to_correlate']
    ):
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
            batch_targets = []

            for i, (doc, start, duration) in enumerate(documents):
                batch_docs.append(doc)

                batch_targets.append(extract_target(start, duration))

                if i == model_settings["batch_eval_size"]:
                    break
            else:
                # It's the last batch
                read_next_batch = False

            # Outliers detection
            agg_outliers = UnivariateOutlier(
                model_settings["trigger_method"],
                model_settings["trigger_sensitivity"],
                model_settings["n_neighbors"]
            ).detect_outliers(np.array(batch_targets))

            for index in agg_outliers:
                process_outlier(
                    batch_docs[index],
                    model_settings,
                    batch_targets[index]
                )

            all_targets[aggregation].extend(batch_targets)
            all_outliers[aggregation].extend([
                a + len(all_outliers[aggregation])
                for a in agg_outliers
            ])

            # Freevalue_iteration the memory
            del batch_docs
            del batch_targets
            # Garbage collector
            gc.collect()

    logging.logger.info('Number of aggregations: %i\t:\t' % len(aggregations))
    logging.logger.info('Number of elements: %i' %
                        sum([len(all_targets[t]) for t in all_targets]))

    if model_settings["plot_graph"]:
        histogram_outliers_agg(
            all_targets,
            all_outliers,
            agg_title=model_settings["aggregator"],
            xlabel=model_settings["target"],
            bins=40,
            yscale='linear'
        )


def get_target_extractor(target):
    '''
    Return a function which can be used to extract the target

    Return
    ======
    function(start, duration) -> target 			For <within_aggregator>
    function(agg_starts, agg_durations) -> target 	For <across_aggregator>
    '''

    #####################
    # ACROSS AGGREGATOR #
    #####################
    if target == 'number_of_events':
        def ret(agg_starts, agg_durations):
            return len(agg_starts)
        return ret

    elif target == 'max_duration':
        def ret(agg_starts, agg_durations):
            return max(agg_durations)
        return ret

    elif target == 'min_duration':
        def ret(agg_starts, agg_durations):
            return min(agg_durations)
        return ret

    elif target == 'mean_duration':
        def ret(agg_starts, agg_durations):
            return np.array(agg_durations).mean()
        return ret

    elif target == 'events_per_minute':
        def ret(agg_starts, agg_durations):
            start_agg = min(agg_starts)
            end_agg = max(agg_starts)
            aggregator_time_range = (
                (end_agg - start_agg).total_seconds() / 60) + 1
            n_events = len(agg_starts) - 1
            return n_events / aggregator_time_range
        return ret

    #####################
    # WITHIN AGGREGATOR #
    #####################
    allowed = [
        'start_timestamp', 'start_year', 'start_month', 'start_day',
        'start_hour', 'start_minute',
        'end_timestamp', 'end_year', 'end_month', 'end_day',
        'end_hour', 'end_minute',
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
            if duration < 0:
                logging.logger.info('Error, negative duration = ' + str(duration))
                duration = 0
            return np.log10(duration+1)

        return ret

    raise Exception('Wrong time target')


def extract_model_settings(section_name):
    model_settings = dict()

    model_settings["plot_graph"] = settings.config.getint(
        'general', "plot_graph")

    model_settings["aggregator"] = settings.config.get(
        section_name, "aggregator")
    model_settings["fields_value_to_correlate"] = settings.config.get(
        section_name, "fields_value_to_correlate").split(',')

    model_settings["es_query_filter"] = settings.config.get(
        section_name, "es_query_filter")

    model_settings["start_condition"] = settings.config.get(
        section_name, "start_condition")
    model_settings["end_condition"] = settings.config.get(
        section_name, "end_condition")

    model_settings["start_condition"] = json.loads(model_settings["start_condition"])
    model_settings["end_condition"] = json.loads(model_settings["end_condition"])

    model_settings["outlier_reason"] = settings.config.get(
        section_name, "outlier_reason")
    model_settings["outlier_type"] = settings.config.get(
        section_name, "outlier_type")
    model_settings["outlier_summary"] = settings.config.get(
        section_name, "outlier_summary")

    model_settings["target"] = settings.config.get(section_name, "target")
    model_settings["trigger_method"] = settings.config.get(
        section_name, "trigger_method")
    model_settings["trigger_sensitivity"] = settings.config.getfloat(
        section_name, "trigger_sensitivity")
    model_settings["batch_eval_size"] = settings.config.getint(
        section_name, "batch_eval_size")

    try:
        model_settings["n_neighbors"] = settings.config.getint(
            section_name, "n_neighbors")
    except Exception:
        model_settings["n_neighbors"] = None

    try:
        model_settings["should_notify"] = settings.config.getboolean(
            "notifier", "email_notifier") and settings.config.getboolean(
            section_name, "should_notify")

    except configparser.NoOptionError:
        model_settings["should_notify"] = False

    return model_settings


def process_outlier(doc, model_settings, target):
    fields = es.extract_fields_from_document(doc)

    outlier_summary = model_settings["outlier_summary"].replace(
        '<target>', str(target))
    outlier_summary = helpers.utils.replace_placeholder_fields_with_values(
        outlier_summary, fields)

    outlier = Outlier(
        type=model_settings["outlier_type"],
        reason=model_settings["outlier_reason"],
        summary=outlier_summary
    )

    es.process_outliers(
        doc=doc,
        outliers=[outlier],
        should_notify=model_settings["should_notify"]
    )

    return outlier
