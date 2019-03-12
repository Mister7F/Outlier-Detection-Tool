import numpy as np
import configparser
import random

from helpers.outlier import Outlier
from helpers.singletons import settings, es, logging
from collections import defaultdict
from collections import Counter
import helpers.utils


def perform_analysis():
    for name in settings.config.sections():
        if name.startswith("terms_"):
            param, model_name = name.split("terms_", 1)
            should_test_model = settings.config.getboolean("general", "run_models") and settings.config.getboolean(name, "run_model")
            should_run_model = settings.config.getboolean("general", "test_models") and settings.config.getboolean(name, "test_model")

            if should_test_model or should_run_model:
                model_settings = extract_model_settings(name)
                if "*" in model_settings["target"]:
                    original_model_name = model_name

                    logging.logger.warning("running terms model in brute force mode, could take a long time!")

                    lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])
                    batch_size = settings.config.getint("terms", "terms_batch_eval_size")

                    total_events = es.count_documents(lucene_query=lucene_query)
                    logging.init_ticker(total_steps=min(total_events, batch_size), desc=model_name + " - extracting brute force fields")

                    field_names = set()
                    num_docs_processed = 0
                    for doc in es.scan(lucene_query=lucene_query):
                        logging.tick()
                        fields = es.extract_fields_from_document(doc)
                        fields = helpers.utils.flatten_dict(fields)

                        # skip all fields that are related to outliers, we don't want to brute force them
                        for field_name in list(fields.keys()):  # create list instead of iterator so we can mutate the dictionary when iterating
                            if field_name.startswith('outliers.'):
                                logging.logger.debug("not brute forcing outliers field " + str(field_name))
                                fields.pop(field_name)

                        field_names.update(fields.keys())

                        if num_docs_processed == batch_size:
                            break
                        else:
                            num_docs_processed += 1

                    logging.logger.info("going to brute force " + str(len(field_names)) + " fields")
                    for field_name in field_names:
                        model_name = original_model_name + " [" + field_name + "]"
                        # only brute force nested fields, so not the top level fields such as timestamp, deployment name, etc.
                        if "." in field_name:
                            model_settings["target"] = list([field_name])
                            model_settings["brute_forced_field"] = field_name  # so it can be added to the outlier events automatically
                            evaluate_model(model_name=model_name, model_settings=model_settings, brute_force=True)

                else:
                    evaluate_model(model_name=model_name, model_settings=model_settings)


def extract_model_settings(section_name):
    model_settings = dict()
    model_settings["es_query_filter"] = settings.config.get(section_name, "es_query_filter")
    model_settings["target"] = settings.config.get(section_name, "target").replace(' ', '').split(",")  # remove unnecessary whitespace, split fields
    model_settings["aggregator"] = settings.config.get(section_name, "aggregator").replace(' ', '').split(",")  # remove unnecessary whitespace, split fields
    model_settings["trigger_on"] = settings.config.get(section_name, "trigger_on")
    model_settings["trigger_method"] = settings.config.get(section_name, "trigger_method")
    model_settings["trigger_sensitivity"] = settings.config.getint(section_name, "trigger_sensitivity")

    model_settings["target_count_method"] = settings.config.get(section_name, "target_count_method")

    model_settings["outlier_reason"] = settings.config.get(section_name, "outlier_reason")
    model_settings["outlier_type"] = settings.config.get(section_name, "outlier_type")
    model_settings["outlier_summary"] = settings.config.get(section_name, "outlier_summary")

    try:
        model_settings["should_notify"] = settings.config.getboolean("notifier", "email_notifier") and settings.config.getboolean(section_name, "should_notify")
    except configparser.NoOptionError:
        model_settings["should_notify"] = False

    # Validate model settings
    if model_settings["target_count_method"] not in {"within_aggregator", "across_aggregators"}:
        raise ValueError("target count method " + model_settings["target_count_method"] + " not supported")

    if model_settings["trigger_on"] not in {"high", "low"}:
        raise ValueError("Unexpected outlier trigger condition " + model_settings["trigger_on"])

    return model_settings


def add_term_to_batch(eval_terms_array, aggregator_value, target_value, observations, doc):
    if aggregator_value not in eval_terms_array.keys():
        eval_terms_array[aggregator_value] = defaultdict(list)

    eval_terms_array[aggregator_value]["targets"].append(target_value)
    eval_terms_array[aggregator_value]["observations"].append(observations)
    eval_terms_array[aggregator_value]["raw_docs"].append(doc)

    return eval_terms_array


def evaluate_model(model_name=None, model_settings=None, brute_force=False):
    if brute_force:
        lucene_query = es.filter_by_query_string(model_settings["es_query_filter"] + " AND _exists_:" + model_settings["brute_forced_field"])
    else:
        lucene_query = es.filter_by_query_string(model_settings["es_query_filter"])

    total_events = es.count_documents(lucene_query=lucene_query)

    logging.print_analysis_intro(event_type="evaluating " + model_name, total_events=total_events)
    logging.init_ticker(total_steps=total_events, desc=model_name + " - evaluating terms model")

    eval_terms_array = defaultdict()
    total_terms_added = 0

    outlier_batches_trend = 0
    for doc in es.scan(lucene_query=lucene_query):
        logging.tick()
        fields = es.extract_fields_from_document(doc)

        try:
            target_sentences = helpers.utils.flatten_fields_into_sentences(fields=fields, sentence_format=model_settings["target"])
            aggregator_sentences = helpers.utils.flatten_fields_into_sentences(fields=fields, sentence_format=model_settings["aggregator"])
            will_process_doc = True
        except (KeyError, TypeError):
            logging.logger.debug("Skipping event which does not contain the target and aggregator fields we are processing. - [" + model_name + "]")
            will_process_doc = False

        if will_process_doc:
            observations = dict()

            if brute_force:
                observations["brute_forced_field"] = model_settings["brute_forced_field"]

            for target_sentence in target_sentences:
                flattened_target_sentence = helpers.utils.flatten_sentence(target_sentence)

                for aggregator_sentence in aggregator_sentences:
                    flattened_aggregator_sentence = helpers.utils.flatten_sentence(aggregator_sentence)
                    eval_terms_array = add_term_to_batch(eval_terms_array, flattened_aggregator_sentence, flattened_target_sentence, observations, doc)

            total_terms_added += len(target_sentences)

        # Evaluate batch of events against the model
        last_batch = (logging.current_step == total_events)
        if last_batch or total_terms_added >= settings.config.getint("terms", "terms_batch_eval_size"):
            logging.logger.info("evaluating batch of " + "{:,}".format(total_terms_added) + " terms")
            outliers = evaluate_batch_for_outliers(terms=eval_terms_array, model_settings=model_settings)

            if len(outliers) > 0:
                unique_summaries = len(set(o.get_observation("summary") for o in outliers))
                logging.logger.info("total outliers in batch processed: " + str(len(outliers)) + " [" + str(unique_summaries) + " unique summaries]")
                outlier_batches_trend += 1
            else:
                logging.logger.info("no outliers detected in batch")
                outlier_batches_trend -= 1

            if outlier_batches_trend == -3 and brute_force:
                logging.logger.info("too many batches without outliers, we are not going to continue brute forcing")
                break

            if outlier_batches_trend == 3 and brute_force:
                logging.logger.info("too many batches with outliers, we are not going to continue brute forcing")
                break

            # Reset data structures for next batch
            eval_terms_array = defaultdict()
            total_terms_added = 0


def evaluate_batch_for_outliers(terms=None, model_settings=None):
    # Initialize
    outliers = list()
    total_terms_processing = 0

    # Count the total number of terms for each aggregator
    for i, aggregator_value in enumerate(terms):
        total_terms_processing += len(terms[aggregator_value]["targets"])

    # In case we want to count terms across different aggregators, we need to first iterate over all aggregators
    # and calculate the total number of unique terms for each aggregated value.
    # For example:
    # terms["smsc.exe"][A, B, C, D, D, E]
    # terms["abc.exe"][A, A, B]
    # is converted into:
    # unique_target_counts_across_aggregators: [5, 2] (the first term contains 5 unique values, the second one contains 2)
    if model_settings["target_count_method"] == "across_aggregators":
        unique_target_counts_across_aggregators = list()

        # loop 0: {i=0, aggregator_value = "smsc.exe"}, loop 1: {i=1, aggregator_value = "abc.exe"},
        for i, aggregator_value in enumerate(terms):
            # unique_targets_in_aggregated_value = loop 0: [A, B, C, D, E], loop 1: [A, A, B]
            # unique_target_counts_across_aggregators = loop 0: [5], loop 1: [5, 2]
            unique_targets_in_aggregated_value = set(terms[aggregator_value]["targets"])
            unique_target_counts_across_aggregators.append(len(unique_targets_in_aggregated_value))

        # Calculate the decision frontier
        # unique_target_counts_across_aggregators = [5, 2]
        decision_frontier = helpers.utils.get_decision_frontier(model_settings["trigger_method"], unique_target_counts_across_aggregators, model_settings["trigger_sensitivity"], model_settings["trigger_on"])
        logging.logger.debug("using " + model_settings["trigger_method"] + " decision frontier " + str(decision_frontier) + " across all aggregators")

        non_outlier_values = set()

        # loop 0: {i=0, aggregator_value = "smsc.exe"}, loop 1: {i=1, aggregator_value = "abc.exe"},
        for i, aggregator_value in enumerate(terms):
            unique_target_count_across_aggregators = unique_target_counts_across_aggregators[i]
            logging.logger.debug("unique target count for aggregator " + str(aggregator_value) + ": " + str(unique_target_count_across_aggregators) + " - decision frontier " + str(decision_frontier))
            is_outlier = helpers.utils.is_outlier(unique_target_count_across_aggregators, decision_frontier, model_settings["trigger_on"])

            if is_outlier:
                for ii, term_value in enumerate(terms[aggregator_value]["targets"]):
                    non_outlier_values_sample = ",".join(random.sample(non_outlier_values, min(3, len(non_outlier_values))))
                    outliers.append(process_outlier(decision_frontier, non_outlier_values_sample, unique_target_count_across_aggregators, terms, aggregator_value, ii, term_value, model_settings))
            else:
                for ii, term_value in enumerate(terms[aggregator_value]["targets"]):
                    non_outlier_values.add(term_value)

    # In case we want to count terms within an aggregator, it's a bit easier.
    # For example:
    # terms["smsc.exe"][A, B, C, D, D, E]
    # terms["abc.exe"][A, A, B]
    # is converted into:
    # First iteration: "smsc.exe" -> counted_target_values: {A: 1, B: 1, C: 1, D: 2, E: 1}
    # For each aggregator, we iterate over all terms within it:
    # term_value_count for a document with term "A" then becomes "1" in the example above.
    # we then flag an outlier if that "1" is an outlier in the array ["1 1 1 2 1"]
    if model_settings["target_count_method"] == "within_aggregator":
        for i, aggregator_value in enumerate(terms):
            # Count percentage of each target value occuring
            counted_targets = Counter(terms[aggregator_value]["targets"])
            counted_target_values = list(counted_targets.values())

            logging.logger.debug("terms count for aggregator value " + aggregator_value + " -> " + str(counted_targets))
            decision_frontier = helpers.utils.get_decision_frontier(model_settings["trigger_method"], counted_target_values, model_settings["trigger_sensitivity"], model_settings["trigger_on"])

            logging.logger.debug("using " + model_settings["trigger_method"] + " decision frontier " + str(decision_frontier) + " for aggregator " + str(aggregator_value))

            non_outlier_values = set()
            for ii, term_value in enumerate(terms[aggregator_value]["targets"]):
                term_value_count = counted_targets[term_value]
                is_outlier = helpers.utils.is_outlier(term_value_count, decision_frontier, model_settings["trigger_on"])

                if is_outlier:
                    non_outlier_values_sample = ",".join(random.sample(non_outlier_values, min(3, len(non_outlier_values))))
                    outliers.append(process_outlier(decision_frontier, non_outlier_values_sample, term_value_count, terms, aggregator_value, ii, term_value, model_settings))
                else:
                    non_outlier_values.add(term_value)
    return outliers


def process_outlier(decision_frontier, non_outlier_values_sample, term_value_count, terms, aggregator_value, ii, term_value, model_settings):
    # Extract fields from raw document
    fields = es.extract_fields_from_document(terms[aggregator_value]["raw_docs"][ii])

    observations = terms[aggregator_value]["observations"][ii]

    observations["non_outlier_values_sample"] = non_outlier_values_sample
    observations["aggregator"] = aggregator_value
    observations["term"] = term_value
    observations["term_count"] = term_value_count
    observations["decision_frontier"] = decision_frontier
    observations["trigger_method"] = str(model_settings["trigger_method"])
    observations["confidence"] = np.abs(decision_frontier - term_value_count)

    merged_fields_and_observations = helpers.utils.merge_two_dicts(fields, observations)

    outlier_summary = helpers.utils.replace_placeholder_fields_with_values(model_settings["outlier_summary"], merged_fields_and_observations)

    outlier_assets = helpers.utils.extract_outlier_asset_information(fields, settings)

    if len(outlier_assets) > 0:
        observations["assets"] = outlier_assets

    outlier = Outlier(type=model_settings["outlier_type"], reason=model_settings["outlier_reason"], summary=outlier_summary)

    for k, v in observations.items():
        outlier.add_observation(k, v)

    es.process_outliers(doc=terms[aggregator_value]["raw_docs"][ii], outliers=[outlier], should_notify=model_settings["should_notify"])
    return outlier