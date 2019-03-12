import random
import numpy as np
import configparser

import helpers.utils
from collections import Counter
from collections import defaultdict
from helpers.outlier import Outlier
from helpers.singletons import settings, es, logging
from helpers.outliers_detection import outliers_detection


def perform_analysis():
    for name in settings.config.sections():
        if name.startswith("terms_"):
            model_settings = extract_model_settings(name)

            if model_settings["target_count_method"] == "across_aggregators":
                perform_analysis_across_aggregators(model_settings)

            elif model_settings["target_count_method"] == "within_aggregator":
                perform_analysis_within_aggregator(model_settings)

            else:
                raise Exception('Wrong target_count_method')


def perform_analysis_within_aggregator(model_settings):
    aggregations = []
    all_targets = {}
    all_counts = {}
    all_outliers = {}

    for aggregation, documents in es.scan_aggregations(
        model_settings["aggregator"],
        model_settings['es_query_filter']
    ):

        aggregations.append(aggregation)
        all_targets[aggregation] = []
        all_counts[aggregation] = []
        all_outliers[aggregation] = []

        read_batch = True

        while read_batch:

            batch_targets = []
            batch_counts = []
            batch_docs = {}

            for i, doc in enumerate(documents):
                target = es.get_field_by_path(doc, model_settings["target"])

                batch_targets.append(target)

                # Keep the first doc for each target
                if hash(target) not in batch_docs:
                    batch_docs[hash(target)] = doc

                if i >= model_settings["batch_size"]:
                    logging.logger.info('Next batch')
                    break

            else:
                # It was the last batch
                read_batch = False

            if not len(batch_targets):
                # If we breack the loop and if it was the last batch
                # Very low probability (1/batch_size) but can happen !
                continue

            batch_targets, batch_counts = np.unique(
                batch_targets,
                return_counts=True
            )
            batch_counts = np.array(batch_counts)

            # Outliers detection
            batch_outliers = outliers_detection(
                batch_counts,
                model_settings["trigger_method"],
                model_settings["trigger_sensitivity"],
                model_settings["n_neighbors"],
                model_settings["trigger_on"]
            )

            # Process outliers
            for outlier in batch_outliers:
                target = batch_targets[outlier]
                doc = batch_docs[hash(target)]
                count = batch_counts[outlier].tolist()

                process_outlier(doc, model_settings, count, aggregation)

            # Get target and count for plotting
            batch_outliers = np.array(batch_outliers) + len(all_targets[aggregation])
            all_outliers[aggregation].extend(batch_outliers)
            all_targets[aggregation].extend(batch_targets)
            all_counts[aggregation].extend(batch_counts)

            # Free memory
            del batch_docs
            del batch_targets
            del batch_counts

    logging.logger.info('Number of aggregations: %i' % len(aggregations))
    logging.logger.info('Number of outliers: %i' % sum(
        [len(all_outliers[a]) for a in all_outliers]))


def perform_analysis_across_aggregators(model_settings):
    lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

    target = model_settings["target"]
    aggregator = model_settings["aggregator"]

    aggregators_target = {}
    aggregations_docs = []

    for doc in es.scan(lucene_query):
        aggregator, target = es.get_fields_by_path(
            doc,
            [model_settings["aggregator"], model_settings["target"]]
        )

        if aggregator not in aggregators_target:
            aggregators_target[aggregator] = []
            aggregations_docs.append(doc)

        if hash(target) not in aggregators_target[aggregator]:
            aggregators_target[aggregator].append(hash(target))

    aggregations_docs = np.array(aggregations_docs)

    aggregations = []
    aggregations_target = []

    for agg in aggregators_target:
        aggregations.append(agg)
        aggregations_target.append(len(aggregators_target[agg]))

    aggregations = np.array(aggregations)
    aggregations_target = np.array(aggregations_target)

    logging.logger.info('Number of aggregations: %i' % len(aggregations))

    # Outliers detection
    outliers = outliers_detection(
        aggregations_target,
        model_settings["trigger_method"],
        model_settings["trigger_sensitivity"],
        model_settings["n_neighbors"],
        model_settings["trigger_on"]
    )

    for outlier in outliers:
        agg = aggregations[outlier]
        # Process only the first doc of the aggregation,
        # this document represent the aggregation...
        process_outlier(
            aggregations_docs[outlier],
            model_settings,
            aggregations_target[outlier].tolist(),
            agg
        )


def extract_model_settings(section_name):
    model_settings = dict()
    model_settings["plot_graph"] = settings.config.getint("general", "plot_graph")
    model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")
    model_settings["target"] = settings.config.get(section_name, "target")
    model_settings["aggregator"] = settings.config.get(section_name, "aggregator")
    model_settings["trigger_method"] = settings.config.get(section_name, "trigger_method")
    try:
        model_settings["trigger_on"] = settings.config.get(section_name, "trigger_on")
    except Exception:
        model_settings["trigger_on"] = None
    model_settings["trigger_sensitivity"] = settings.config.getint(section_name, "trigger_sensitivity")

    model_settings["target_count_method"] = settings.config.get(section_name, "target_count_method")

    model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
    model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
    model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

    model_settings["batch_size"] = settings.config.getint(section_name, "batch_size")

    try:
        model_settings["should_notify"] = settings.config.getboolean("notifier", "email_notifier") and settings.config.getboolean(section_name, "should_notify")
    except configparser.NoOptionError:
        model_settings["should_notify"] = False

    try:
        model_settings["n_neighbors"] = settings.config.getint(section_name, "n_neighbors")
    except Exception:
        model_settings["n_neighbors"] = -1

    return model_settings


def process_outlier(doc, model_settings, count, aggregator):
    fields = es.extract_fields_from_document(doc)

    observations = {}
    observations["term_count"] = count
    observations["aggregator"] = aggregator

    merged_fields_and_observations = helpers.utils.merge_two_dicts(fields, observations)

    outlier_summary = helpers.utils.replace_placeholder_fields_with_values(model_settings["outlier_summary"], merged_fields_and_observations)

    outlier_assets = helpers.utils.extract_outlier_asset_information(fields, settings)

    if len(outlier_assets) > 0:
        observations["assets"] = outlier_assets

    outlier = Outlier(type=model_settings["outlier_type"], reason=model_settings["outlier_reason"], summary=outlier_summary)

    for k, v in observations.items():
        outlier.add_observation(k, v)

    es.process_outliers(doc=doc, outliers=[outlier], should_notify=model_settings["should_notify"])
    return outlier
