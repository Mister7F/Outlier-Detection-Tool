import re
import numpy as np
import helpers.utils
from collections import defaultdict
from helpers.outlier import Outlier
from configparser import NoOptionError
from helpers.utils import is_base64_encoded
from helpers.singletons import settings, es, logging
from helpers.outliers_detection import outliers_detection


def perform_analysis():
    for section_name in settings.config.sections():
        if section_name.startswith("metrics_"):
            model_settings = extract_model_settings(section_name)

            logging.logger.info('# ' + section_name + ' #')
            logging.logger.info('Metric: ' + model_settings['metric'])

            for aggregation, documents in es.scan_aggregations(
                model_settings["aggregator"],
                model_settings['es_query_filter']
            ):

                # For all batch
                read_batch = True
                while read_batch:

                    metrics = []
                    docs = []

                    for i, doc in enumerate(documents):
                        target = es.get_field_by_path(
                            doc,
                            model_settings["target"]
                        )

                        metric = extract_metrics(target, model_settings['metric'])

                        if metric is None:
                            continue

                        metrics.append(metric)
                        docs.append(doc)

                        if i >= model_settings["batch_size"]:
                            break

                    else:
                        # It was the last batch
                        read_batch = False

                    metrics = np.array(metrics)
                    docs = np.array(docs)

                    outliers = outliers_detection(
                        metrics,
                        model_settings["trigger_method"],
                        model_settings["trigger_sensitivity"],
                        model_settings["n_neighbors"],
                        model_settings["trigger_on"]
                    )

                    # Process outliers
                    for outlier in outliers:
                        process_outlier(
                            docs[outlier],
                            metrics[outlier],
                            model_settings
                        )


def extract_metrics(target, metric):

    if metric == 'numerical_value':
        try:
            target = float(target)
        except ValueError:
            return None

    elif metric == 'length':
        target = len(target)

    elif metric == 'entropy':
        target = helpers.utils.shannon_entropy(target)

    elif metric.startswith('regex_len_'):
        regex = metric[10:]
        target = re.search(regex, target)
        target = len(target.group()) if target else 0

    elif metric.startswith('regex_count_match_'):
        regex = metric[18:]
        target = len(re.findall(regex, target))

    elif metric.startswith('regex_sum_len_'):
        regex = metric[14:]
        target = sum(
            len(i)
            for i in re.findall(regex, target)
        )

    elif metric == 'base64_encoded_length':
        target_value_words = re.split(
            "[^A-Za-z0-9+/=]", str(target))

        target = [0]

        for word in target_value_words:
            decoded_word = is_base64_encoded(word)

            if decoded_word and len(decoded_word) >= 10:
                target.append(len(decoded_word))

        target = max(target)

    elif metric == 'hex_encoded_length':
        words = re.split("[^a-fA-F0-9+]", str(target))
        lengths = [0]
        for word in words:
            if len(word) > 10 and helpers.utils.is_hex_encoded(word):
                lengths.append(len(word))

        target = max(lengths)

    else:
        raise Exception('Wrong metric !')

    return target


def extract_model_settings(section_name):
    model_settings = dict()
    model_settings["plot_graph"] = settings.config.getint(
        "general", "plot_graph")
    model_settings["es_query_filter"] = settings.config.get(
        section_name, "es_query_filter")
    model_settings["target"] = settings.config.get(section_name, "target")

    model_settings["aggregator"] = settings.config.get(
        section_name, "aggregator")
    model_settings["metric"] = settings.config.get(section_name, "metric")

    model_settings["trigger_method"] = settings.config.get(
        section_name, "trigger_method")
    model_settings["trigger_sensitivity"] = settings.config.getint(
        section_name, "trigger_sensitivity")

    try:
        model_settings["trigger_on"] = settings.config.get(section_name, "trigger_on")
    except Exception:
        model_settings["trigger_on"] = None

    model_settings["outlier_reason"] = settings.config.get(
        section_name, "outlier_reason")
    model_settings["outlier_type"] = settings.config.get(
        section_name, "outlier_type")
    model_settings["outlier_summary"] = settings.config.get(
        section_name, "outlier_summary")

    try:
        model_settings["n_neighbors"] = settings.config.getint(
            section_name, "n_neighbors")
    except Exception:
        model_settings["n_neighbors"] = -1

    model_settings["batch_size"] = settings.config.getint(
        section_name, "batch_size")

    try:
        model_settings["should_notify"] = settings.config.getboolean(
            "notifier", "email_notifier") and settings.config.getboolean(
            section_name, "should_notify")
    except NoOptionError:
        model_settings["should_notify"] = False

    return model_settings


def process_outlier(doc, metric_value, model_settings):

    fields = es.extract_fields_from_document(doc)

    outlier_summary = helpers.utils.replace_placeholder_fields_with_values(
        model_settings["outlier_summary"], fields)

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
