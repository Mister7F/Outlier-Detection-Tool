import os
import math
import numpy as np
import matplotlib; matplotlib.use('agg')
import matplotlib.pyplot as plt
import seaborn as sns


sns.set(color_codes=True)
sns.set(style="whitegrid")


def histogram(data, labels, xlabel='Value', ylabel='Count', bins=40,
              log=True, show=False, filename=None, title='Histogram'):
    fig = plt.figure()

    xlabel = ' '.join(xlabel.split('_'))
    xlabel = xlabel[0].upper() + xlabel[1:]

    binwidth = (max([d.max() for d in data]) - min([d.min() for d in data])) / bins

    if math.isclose(binwidth, 0):
        binwidth = 1

    for points, label, color in zip(data, labels, ['b', 'r']):
        bins = int((points.max() - points.min())/binwidth)+1
        sns.distplot(points, color=color, label=label, bins=bins, kde=False, hist_kws=dict(alpha=1))

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if log:
        plt.yscale('log')

    plt.legend()

    if show:
        plt.show()

    if filename is not None:
        if not os.path.exists(os.path.split(filename)[0]):
            os.mkdir(os.path.split(filename)[0])
        plt.savefig(filename)

    plt.cla()
    plt.clf()


def bar(data, names, labels, xlabel='Count',
        ylabel='Label', scale='log', title='Bar',
        max_label_len=10, filename=None, show=False):

    fig, ax = plt.subplots()

    y_pos = np.arange(sum([d.shape[0] for d in data]))
    pos = 0

    for color, points, label in zip(['b', 'r'], data, labels):
        ax.barh(
            y_pos[pos:pos+len(points)],
            points,
            align='center',
            label=label
        )
        pos += len(points)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([n[:max_label_len] for name in names for n in name])
    ax.invert_yaxis()

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xscale(scale)
    ax.set_xlim(0.5)
    ax.set_title(title)

    plt.subplots_adjust(left=0.3, right=0.8, top=0.8, bottom=0.2)

    plt.legend()

    if show:
        plt.show()

    if filename is not None:
        if not os.path.exists(os.path.split(filename)[0]):
            os.mkdir(os.path.split(filename)[0])
        plt.savefig(filename)

    plt.cla()
    plt.clf()

#######
# OLD #
#######


def histogram_outliers(data, outliers=[], xlabel='Value', bins=10,
                       yscale='linear', ylabel='Count',
                       filename=None, show=True):
    '''
    Params
    ======
    - data (np.array) : 1D Vector which contains all values
    - outliers (list) : List of outliers index in data
    - xlabel    (str) : Label used for the X-axis and for the title
    - bins      (int) : Number of columns
    - yscale    (str) : linear, log, logit,...
    '''
    xlabel = ' '.join(xlabel.split('_'))
    xlabel = xlabel[0].upper() + xlabel[1:]

    if not len(outliers):
        plt.hist(
            data,
            bins=bins,
            label='Data',
            color='darkblue',
            stacked=True
        )
    else:
        plt.hist(
            [data[outliers], np.delete(data, outliers)],
            bins=bins,
            label=['Outliers', 'Data'],
            color=['r', 'darkblue'],
            stacked=True
        )

    plt.title(xlabel + ' - Histogram')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.yscale(yscale)
    plt.ylim(bottom=0.1)
    plt.legend()

    if show:
        plt.show()

    if filename is not None:
        if not os.path.exists(os.path.split(filename)[0]):
            os.mkdir(os.path.split(filename)[0])
        plt.savefig(filename)

    plt.cla()
    plt.clf()


def histogram_outliers_agg(agg_data, agg_outliers, one_plot_per_agg=True,
                           agg_title='Aggregation', xlabel='Value',
                           bins=40, yscale='linear'):
    '''
    - agg_data         (dict) : {'aggregator' : np.array(data)}
    - agg_outliers     (dict) : {'aggregator' : <outliers index>}
    - one_plot_per_agg (bool) : If false, draw all data in the same plot
    - agg_title         (str) : Used to build the title
    - xlabel            (str) : Label used for the X-axis and for the title
    - bins              (int) : Number of columns
    - yscale            (str) : linear, log, logit,...
    '''

    if not one_plot_per_agg:
        raise Exception('Not yet implemented')

    n_cols = min(3, len(agg_data))
    n_rows = math.ceil(len(agg_data) / n_cols)

    if n_rows > 20:
        raise Exception('Too many aggregations...')

    plt.gcf().subplots_adjust(hspace=1)

    for i, aggregation in enumerate(agg_data):
        plt.subplot(n_rows, n_cols, i+1)

        xlabel = ' '.join(xlabel.split('_'))
        xlabel = xlabel[0].upper() + xlabel[1:]

        data = np.array(agg_data[aggregation])
        out = agg_outliers[aggregation]

        p_data = np.delete(data, out)
        p_out = data[out]

        if not p_out.size:
            plt.hist(p_data, bins=bins, label=[
                     'Data'], color=['darkblue'], stacked=True)
        else:
            plt.hist(
                [p_out, p_data],
                bins=bins,
                label=['Outliers', 'Data'],
                color=['r', 'darkblue'],
                stacked=True
            )

        plt.title(agg_title + ': ' + str(aggregation) +
                  ' - ' + xlabel + ' - Histogram')
        plt.xlabel(xlabel)
        plt.yscale(yscale)
        plt.ylabel('Count' if yscale == 'linear' else 'Count [log]')
        plt.legend()

    plt.show()

    plt.cla()
    plt.clf()


def bar_outliers(values, labels, outliers, xlabel='', ylabel='',
                 title='', filename=None, show=True, scale='log'):

    plt.rcdefaults()
    fig, ax = plt.subplots()

    y_pos = np.arange(len(labels))

    ax.barh(
        np.delete(y_pos, outliers),
        np.delete(values, outliers),
        align='center'
    )

    ax.barh(
        y_pos[outliers],
        values[outliers],
        align='center'
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xscale(scale)
    ax.set_xlim(0.1)
    ax.set_title(title)

    plt.subplots_adjust(left=0.3, right=0.8, top=0.9, bottom=0.1)

    if show:
        plt.show()

    if filename is not None:
        if not os.path.exists(os.path.split(filename)[0]):
            os.mkdir(os.path.split(filename)[0])
        plt.savefig(filename)

    plt.close(fig)
