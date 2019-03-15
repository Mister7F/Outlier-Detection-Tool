import os
import re
from flask import Flask, render_template, send_from_directory


app = Flask(__name__)


@app.route('/imgs/<use_case>/<img>')
def imgs(use_case, img):
    use_cases = os.listdir('../plots')
    if use_case not in use_cases:
        return 'Wrong use case'

    imgs = os.listdir('../plots/' + use_case)

    if img not in imgs or not img.endswith('.svg'):
        return 'Error'

    return send_from_directory('../plots/' + use_case, img)


@app.route('/use_case/<use_case>')
def use_case(use_case):
    use_cases = os.listdir('../plots')
    if use_case not in use_cases:
        return 'Wrong use case'

    imgs = os.listdir('../plots/' + use_case)

    imgs = [
        (i, i.startswith('*'), float(i.split('_')[-2]) < 0.00001)
        for i in imgs if i.endswith('.svg')
    ]

    return render_template(
        'use_case.html.j2',
        use_case=use_case,
        imgs=imgs
    )


@app.route('/')
def index():
    use_cases = os.listdir('../plots')
    return render_template(
        'index.html.j2',
        use_cases=use_cases
    )


if __name__ == '__main__':
    app.run(debug=True)
