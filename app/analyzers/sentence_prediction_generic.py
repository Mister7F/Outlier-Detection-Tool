import numpy as np
from functools import reduce
import re

from helpers.singletons import settings, es, logging
from helpers.text_processing import class_to_id, Tokenizer
from analyzers.ml_models.dense_network import DenseNetwork
from analyzers.algorithms.outliers_error_based import OutliersErrorBased

import keras
from keras import Model
from keras.models import Sequential
from keras.layers import *


def extract_model_settings(section_name):
    model_settings = dict()

    model_settings["outlier_reason"] = settings.config.get(
        section_name, "outlier_reason")
    model_settings["outlier_type"] = settings.config.get(
        section_name, "outlier_type")
    model_settings["outlier_summary"] = settings.config.get(
        section_name, "outlier_summary")

    model_settings["es_query_filter"] = settings.config.get(
        section_name, "es_query_filter")
    model_settings["aggregator"] = settings.config.get(
        section_name, "aggregator")
    model_settings["target"] = settings.config.get(section_name, "target")
    model_settings["tokenizer_split_path"] = settings.config.get(
        section_name, "tokenizer_split_path").split(',')
    model_settings["tokenizer_max_dic_size"] = settings.config.getint(
        section_name, "tokenizer_max_dic_size")
    model_settings["path_regex"] = settings.config.get(
        section_name, "path_regex")
    model_settings["path_truncation"] = settings.config.getint(
        section_name, "path_truncation")

    return model_settings


def perform_analysis():
    for section_name in settings.config.sections():
        if section_name != 'sentence_prediction':
            continue

        logging.logger.info('#######################')
        logging.logger.info('# Sentence prediction #')
        logging.logger.info('#######################')

        model_settings = extract_model_settings(section_name)

        lucene_query = es.filter_by_query_string(
            model_settings["es_query_filter"])
        total_events = es.count_documents(lucene_query=lucene_query)

        logging.logger.info('Total events %i' % total_events)

        fields = [model_settings["aggregator"], model_settings["target"]]

        dataset = np.array([
            es.get_fields_by_path(doc, fields)
            for i, doc in enumerate(es.scan(
                lucene_query=lucene_query,
                query_fields=fields
            ))
            if i < settings.config.getint("general", "es_terminate_after")
        ]).astype('object')

        # Change each process by an id
        x_data, process_dic = class_to_id(dataset[:, 0], return_dic=True)

        '''
        Let's inject some anomalies
        '''
        logging.logger.info('----> ' + dataset[2, 0])
        dataset[2, 1] = 'This/is/a/wrong/path/This/is/a/wrong/path'
        logging.logger.info('----> ' + dataset[49, 0])
        dataset[49, 1] = 'Dangerous/Malware/This/path/is/anormal/I/think'
        logging.logger.info('----> ' + dataset[50, 0])
        dataset[50, 1] = 'Desktop/mymalware/supermalware'
        logging.logger.info('----> ' + dataset[51, 0])
        dataset[51, 1] = 'C://Bureau/wrong_directory/badpath'

        # Extact path from command line
        for i in range(dataset.shape[0]):
            dataset[i, 1] = dataset[i, 1].lstrip()
            groups = re.findall(model_settings["path_regex"], dataset[i, 1])
            if len(groups):
                dataset[i, 1] = groups[0][0]
            else:
                dataset[i, 1] = 'no_regex_match - ' + dataset[i, 1]

        # Tokenize sentences, split in words and replace each words by an id
        tokenizer = Tokenizer(
            split=model_settings["tokenizer_split_path"],
            vocab_size=model_settings["tokenizer_max_dic_size"]
        )

        tokenizer.train_on_data(dataset[:, 1])

        # [process index, word index, word vector]
        y_data = tokenizer.tokenize(dataset[:, 1], onehot=True)

        logging.logger.info(
            str(len(y_data))
            + ' - '
            + str(len(y_data[0]))[:7]
            + ' - '
            + str(len(y_data[0][0]))[:20]
        )

        # Sum
        y_sum = np.array([
            np.array(vec).sum(axis=0)
            for vec in y_data
        ])

        # Truncate or add padding
        # And add sum vector
        y_data = np.array([
            y[:model_settings["path_truncation"]]
            if y.shape[0] > model_settings["path_truncation"]
            else np.vstack((y, np.zeros((model_settings["path_truncation"]-y.shape[0], y.shape[1]))))
            for y in y_data
        ])

        # Add sum vector
        y_data = np.array([
            np.vstack((y, s))
            for y, s in zip(y_data, y_sum)
        ])

        logging.logger.info('Input shape  %s' % str(x_data.shape))
        logging.logger.info('Output shape %s' % str(y_data.shape))
        logging.logger.info('Number of differents processes %i' % x_data.max())

        # Flatten
        y_data = y_data.reshape(y_data.shape[0], -1)
        logging.logger.info('Output shape flattened %s' % str(y_data.shape))

        input = Input(shape=(1,), name='process_id')
        embed = Embedding(x_data.max()+1, 1024, input_length=1,
                          name='process_vectors')(input)
        layer = Flatten(name='flat')(embed)

        direc = Dense(y_data.shape[1]-y_sum.shape[1],
                      activation='relu', name='first_directories')(layer)
        l_sum = Dense(y_sum.shape[1], activation='relu',
                      name='sum_vector')(layer)

        output = Concatenate(name='concat')([direc, l_sum])

        model = Model(inputs=[input], outputs=[output])

        model.compile('sgd', 'mse')

        model.fit(x_data, y_data, validation_split=0, epochs=5)

        # Show biggest error
        y_pred = model.predict(x_data)
        errors = np.square(y_pred-y_data).sum(axis=1)

        outliers = np.argsort(errors)[::-1]

        logging.logger.info('30 Biggest errors')
        prev = []
        for process_index in outliers[:50]:
            if prev == dataset[process_index, :].tolist():
                continue
            prev = dataset[process_index, :].tolist()
            logging.logger.info(str(errors[process_index])[
                                :4] + '\t' + dataset[process_index, 0][:11] + '\t\t' + dataset[process_index, 1][:100])

        # Show the model
        from keras.utils import plot_model
        plot_model(
            model,
            to_file='/shared/model_anormal_cmdlines.png',
            show_shapes=True
        )
