#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from os import environ
from time import strftime, strptime, gmtime

import matplotlib.pyplot as plt
import numpy
import requests
from matplotlib.pyplot import barh, legend, subplots
from matplotlib.ticker import StrMethodFormatter
from PIL import Image
from wordcloud import WordCloud


BASE_URL = environ.get('BASE_URL', 'https://api.qmk.fm/v1/metrics/')

if len(sys.argv) > 1:
    file_date = sys.argv[1]
    year = int(file_date[:4])
    month = int(file_date[4:6])
    day = int(file_date[4:8])
    report_time = strptime('20201222', '%Y%m%d')
else:
    report_time = gmtime()

file_date = strftime('%Y%m%d', report_time)
title_date = strftime('%Y %b %d', report_time)
full_datetime = strftime('%Y %b %d %H:%M:%S %z', report_time)
report_dir = Path('reports') / file_date
regenerating = False

print(f'Generating report for {full_datetime} in {report_dir}')


def get_metric_label(metric_name):
    """Returns the short label for the metric.
    """
    if 'geoip' in metric_name:
        app, geoip, location = metric_name.split('.', 2)

        return location

    app, function, keyboard, layout = metric_name.split('.', 3)

    return keyboard


def prepare_data(data, percent=False):
    """Massage data into a format that matplot likes
    """
    labels = [get_metric_label(l) for l in sorted(data, key=data.get)]
    text_labels = [f'{get_metric_label(l)}:{int(data[l])}' for l in sorted(data, key=data.get)]
    sizes = list(sorted(data.values()))

    return labels, text_labels, sizes


def generate_word_cloud(words, filename):
    """Generate a word cloud from data.

    Args:

        words
            A dictionary where the key is a word and the value is how often that word appears.
    """
    mask = numpy.array(Image.open('qmk_outline.png'))
    wc = WordCloud(background_color="white", max_words=2000, mask=mask, contour_width=2, contour_color='black')
    wc.generate_from_frequencies(words)
    plt.imshow(wc, interpolation="bilinear")
    plt.axis('off')
    plt.savefig(filename, bbox_inches='tight', dpi=257)
    plt.close()


def generate_horizontal_bar_chart(text_labels, sizes, filename):
    """Generate a horizontal bar chart from data.
    """
    height = len(text_labels) * .25
    y_pos = list(range(len(text_labels)))

    fig = plt.figure(figsize=(8, height))
    plt.autoscale(enable=True, axis='y', tight=True)
    bar_graph = plt.barh(y=y_pos, width=sizes, tick_label=text_labels)
    plt.savefig(filename, bbox_inches='tight')
    plt.close()


def fetch_metrics(category):
    """Fetches a set of metrics from the API or disk.
    """
    category_json = report_dir / f'{category}.json'

    if category_json.exists():
        # Return metrics from disk
        print('Report data already found on disk, re-generating report.')
        global regenerating
        regenerating = True

        return read_metrics(category_json)

    # Fetch metrics from API
    url = BASE_URL + category
    data = requests.get(url).json()

    if category in data:
        write_metrics(data[category], category_json)
        return data[category]

    return data


def read_metrics(category_json):
    """Read the metrics from disk.
    """
    return json.load(category_json.open('r'))


def write_metrics(data, category_json):
    """Writes the metrics to disk.
    """
    return json.dump(data, category_json.open('w'))


if __name__ == '__main__':
    if not report_dir.exists():
        report_dir.mkdir()

    # Write out the raw data and the pie charts
    for category in ('keyboards', 'locations'):
        data = fetch_metrics(category)
        category_json = report_dir / f'{category}.json'
        json.dump(data, category_json.open('w'))

        if data:
            labels, text_labels, sizes = prepare_data(data)
            generate_horizontal_bar_chart(text_labels, sizes, f'{report_dir}/{category}.svg')
            generate_word_cloud(dict(zip(labels, sizes)), f'{report_dir}/{category}_wordcloud.png')

    # Write the report md
    if not regenerating:
        index_md = f"""# QMK Statistics For {title_date}

This page shows usage of the QMK Configurator for the 24 hour period ending {full_datetime}.

# Keyboard Compiles

This chart shows all keyboards that were compiled today.

<img src="{report_dir}/keyboards.svg">

Raw data: [JSON]({report_dir}/keyboards.json ':ignore')

# Locations

This chart shows where users using QMK Configurator came from today.

<img src="{report_dir}/locations.svg">

Raw data: [JSON]({report_dir}/locations.json ':ignore')
    """
        (report_dir / 'index.md').write_text(index_md)

        # Update the sidebar
        sidebar = []
        for dir in Path('reports').iterdir():
            if dir.is_dir:
                sidebar.append(f'    * [{dir.name}]({dir}/index.md)')

        sidebar = ["* Reports", *sorted(sidebar)]

        Path('_summary.md').write_text('\n'.join(sidebar))
