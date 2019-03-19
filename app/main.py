import os
import json
import yaml
import argparse

import helpers.print_tools
from readers.es_reader import ES
from helpers.print_tools import *
from analyzers import sql_analyzer


def main():
    args = arg_parse()
    if args['config'] == '*':
        for conf_file in os.listdir('../conf'):
            settings = load_settings(f"../conf/{conf_file}")

            reader = load_reader(settings['reader'])

            for model in settings['models']:
                print(model['name'], type='title')
                sql_analyzer.perform_analysis(reader, model)
    else:
        settings = load_settings(f"../conf/{args['config']}")

        reader = load_reader(settings['reader'])

        for model in settings['models']:
            print(model['name'], type='title')
            sql_analyzer.perform_analysis(reader, model)


def load_settings(filename):
    '''
    Load a configuration file

    Params
    ======
    - filename (str): Filename of the configuration file

    Return
    ======
    dict[section_name][param_name]
    '''
    if not os.path.isfile(filename):
        raise Exception(f'Configuration file not found [{filename}]')

    settings = yaml.safe_load(open(filename, 'r'))

    return settings


def arg_parse():
    '''
    Parse the arguments

    Raturn
    ======
    dict[arg_name]
    '''
    arg_parser = argparse.ArgumentParser(description='Outlier detection tool')

    arg_parser.add_argument(
        '--config',
        help='Configuration file',
        required=True
    )

    arg_parser.add_argument(
        '--mode',
        help='Running mode',
        required=True,
        choices=['interactive', 'deamon', 'tests']
    )

    return vars(arg_parser.parse_args())


def load_reader(params):
    if params['type'] == 'ES':
        return ES(params['url'], params['scroll_size'], params['timeout'])

    else:
        raise Exception('Wrong reader type, check your configuration file')


if __name__ == '__main__':
    intro_message()
    main()
