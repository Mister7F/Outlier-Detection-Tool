import numpy as np

from helpers import plotter
from helpers.print_tools import *
from helpers.metrics_extractor import read_metrics
from helpers.outliers_detection import outlier_detection


def perform_analysis(reader, settings):
    str_targets = settings['targets']
    settings = _convert_cols_name_to_index(reader, settings)
    n_rows = reader.n_rows(settings['sql_query'])

    i_row = 0

    for bucket, rows in reader.sql_query_bucket(
        settings['sql_query'],
        settings['bucket']
    ):
        read_batch = True
        i_batch = 0
        while read_batch:
            batch_rows = []

            for i, row in enumerate(rows):
                print_progress(i_row, n_rows, prefix='Batch %i' % i_batch)
                i_row += 1
                row = read_metrics(row, settings['metrics'])

                # We must ignore this row
                if row is None or None in row:
                    continue

                batch_rows.append(row)

                if i >= settings['batch_size']:
                    break

            else:
                # It was the last batch
                read_batch = False

            # Everything was skipped
            if not batch_rows:
                continue

            batch_rows = np.array(batch_rows, dtype='object')

            outliers = outlier_detection(
                settings['detection'],
                batch_rows[:, settings['targets']]
            )

            process_outliers(batch_rows, outliers, settings)

            i_batch += 1

            if 'plotting' in settings and settings['plotting']['enable']:
                prefix = '*' if len(outliers) else ''
                std = batch_rows[:, settings['targets']].std()
                plotter.histogram(
                    batch_rows[:, settings['targets']],
                    outliers,
                    labels=['Data', 'Outliers'],
                    filename=(f"../{settings['plotting']['output']}/"
                              f"{settings['name']}/{prefix}{'-'.join(bucket)}"
                              f"[{i_batch}]({std}).svg"),
                    title=(settings['name']
                           + (' | ' + '-'.join(bucket)) if settings['bucket']
                           else settings['name']),
                    xlabel=(' - '.join(str_targets) + ' | '
                            + settings['detection']['method'])
                )

            # Clear the memory
            del batch_rows
            del outliers


def _convert_cols_name_to_index(reader, settings):
    '''
    Modify settings to use index and not the column name
    '''
    cols = reader.columns(settings['sql_query'])
    cols = {c: i for i, c in enumerate(cols)}
    settings['bucket'] = [cols[b] for b in settings['bucket']]
    settings['targets'] = [cols[b] for b in settings['targets']]

    summary = settings['outlier_message']['content']
    for i in cols:
        summary = summary.replace('{%s}' % i, '{%i}' % cols[i])
    settings['outlier_message']['content'] = summary

    return settings


def process_outliers(rows, outliers, settings):
    '''
    Params
    ======
    - rows (np.array): Rows returned by the SQL query
    - outliers (list): List of index considered as outlier
    '''
    if not len(outliers):
        return

    print('Number of elements: ', rows.shape[0])
    print('Number of outliers:', len(outliers))
    print('Contamination: %.2f%%' % (len(outliers) * 100 / rows.shape[0]))

    outlier_message = settings['outlier_message']
    for outlier in outliers:
        print('    ', outlier_message['title'])
        print('    ', outlier_message['content'].format(*rows[outlier, :]))
