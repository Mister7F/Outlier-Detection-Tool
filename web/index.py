import os
import re
import json
import math
import shutil
from flask import Flask, render_template, send_from_directory, redirect


app = Flask(__name__)


@app.route('/page/<use_case>/<int:page_size>/<int:page_number>/<int:hide_no_outlier>/<int:hide_one_col>')
@app.route('/page/<use_case>/<int:page_size>/<int:page_number>/<int:hide_no_outlier>/<int:hide_one_col>/<search>')
def page(use_case, page_size, page_number,
         hide_no_outlier, hide_one_col, search=''):
    use_cases = os.listdir('../plots')
    if use_case not in use_cases:
        return 'Wrong use case'

    files = os.listdir('../plots/' + use_case)
    files = [f for f in files if f != '_general.json']

    data = {}

    for f in files:
        plot = '.'.join(f.split('.')[:-1])

        if plot not in data:
            data[plot] = {}

        if f.endswith('.json'):
            j = json.load(open('../plots/' + use_case + '/' + f))
            data[plot].update(j)
        elif f.endswith('.svg'):
            data[plot]['img'] = use_case + '/' + f

    data = {
        k: data[k] for k in data
        if not (hide_no_outlier and not data[k]['n_outliers'])
        and not (hide_one_col and data[k]['one_col'])
    }
    if len(search):
        data = {
            k: data[k] for k in data
            if search.lower() in k.lower()
        }
    total_plots = len(data)
    keys = sorted(list(data.keys()))
    keys = keys[page_number * page_size:(page_number + 1) * page_size]
    data = {k: data[k] for k in keys}
    data = {
        'plots': data,
        'n_pages': math.ceil(total_plots / page_size)
    }

    return json.dumps(data)


@app.route('/files/<use_case>/<file>')
def files(use_case, file):
    use_cases = os.listdir('../plots')
    if use_case not in use_cases:
        return 'Wrong use case'

    files = os.listdir('../plots/' + use_case)

    if file not in files or not (file.endswith('.svg') or file.endswith('.json')):
        return 'Error'

    return send_from_directory('../plots/' + use_case, file)


@app.route('/use_case/<use_case>')
def use_case(use_case):
    use_cases = os.listdir('../plots')
    if use_case not in use_cases:
        return 'Wrong use case'

    files = os.listdir('../plots/' + use_case)

    return render_template(
        'use_case.html.j2',
        use_case=use_case,
        n_files=(len(files) - 1) // 2
    )


@app.route('/delete/<use_case>')
def delete(use_case):
    files = os.listdir('../plots/')
    if use_case not in files:
        return 'Wrong usecase'
    shutil.rmtree('../plots/' + use_case, ignore_errors=True)
    return redirect('/')


@app.route('/')
def index():
    use_cases = os.listdir('../plots')

    metadata = {
        use_case: json.load(open('../plots/' + use_case + '/_general.json'))
        if os.path.isfile('../plots/' + use_case + '/_general.json') else {}
        for use_case in use_cases
    }

    for use_case in use_cases:
        metadata[use_case]['n_outliers'] = 0
        for file in os.listdir('../plots/' + use_case):
            if file.endswith('.json') and not file.startswith('_'):
                tmp = json.load(open('../plots/' + use_case + '/' + file))
                metadata[use_case]['n_outliers'] += tmp['n_outliers']

    return render_template(
        'index.html.j2',
        use_cases=use_cases,
        metadata=metadata
    )


if __name__ == '__main__':
    app.run(debug=True)
