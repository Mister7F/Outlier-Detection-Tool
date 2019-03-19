import os
import math
import numpy as np
import matplotlib; matplotlib.use('agg')
import matplotlib.pyplot as plt


matplotlib.style.use('seaborn-white')

colors = ['#34495e', '#e74c3c', '#2ecc71', '#95a5a6', '#3498db', '#9b59b6']
title_size = 19
legend_size = 13
axis_label_size = 17


def histogram(data, outliers, labels, title='Histogram', xlabel='Value',
              bins=40, log=True, filename=None, show=False):
    data = np.array(data).reshape(-1)
    std = data.std()
    outliers = np.array(outliers).astype(int)
    data = [
        np.delete(data, outliers),
        data[outliers]
    ]

    fig = plt.figure()
    fig.patch.set_alpha(0)

    if std < 0.000001:
        plt.ylim(bottom=0.7)

    plt.hist(
        data,
        color=colors[:len(data)],
        label=labels,
        bins=bins,
        density=False
    )

    plt.title(title, fontsize=title_size)

    xlabel = ' '.join(xlabel.split('_')).capitalize()
    plt.xlabel(xlabel, fontsize=axis_label_size)

    if log:
        plt.yscale('log')

    plt.ylabel('Count', fontsize=axis_label_size)
    plt.legend(fontsize=legend_size)

    plt.gca().patch.set_alpha(0)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)

    if show:
        plt.show()

    if filename is not None:
        if not os.path.exists(os.path.split(filename)[0]):
            os.mkdir(os.path.split(filename)[0])
        plt.savefig(filename, transparent=True, edgecolor='none')

    plt.close()
