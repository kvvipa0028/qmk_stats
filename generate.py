#!/usr/bin/env python3

import json
from pathlib import Path
from os import environ
from time import strftime

import requests
from matplotlib.pyplot import legend, subplots


BASE_URL = environ.get('BASE_URL', 'http://localhost:5000/api/v1/metrics/')


def get_metric_label(metric_name):
    """Returns the short label for the metric.
    """
    if 'geoip' in metric_name:
        app, geoip, location = metric_name.split('.', 2)
        return location

    app, function, keyboard, layout = metric_name.split('.', 3)
    return keyboard


def generate_pie_chart(data, filename):
    """Generates a pie chart from data.
    """
    text_labels = [f'{get_metric_label(l)}:{data[l]}' for l in sorted(data)]
    total = sum(data.values())
    sizes = [(data[i] / total) for i in sorted(data)]

    # Plot the data
    fig1, ax1 = subplots()
    wedges, labels, fractions = ax1.pie(sizes, labeldistance=1.01, startangle=90, counterclock=False, autopct='%1.1f%%', pctdistance=0.87, rotatelabels=True, textprops={'fontsize': 'xx-small'})
    ax1.axis('equal')

    # Add a legend
    fig1.legend(wedges, text_labels, loc="center right", ncol=2, fontsize='xx-small', bbox_to_anchor=(1.35,0.5), title='Starts At Top Center')

    # Rotate the fraction labels to match the keyboard name
    for i in range(len(labels)):
        fractions[i].set_rotation(labels[i].get_rotation())

    # Save the file
    fig1.savefig(filename, bbox_inches='tight')


def fetch_metrics(category):
    """Fetches a set of metrics from the API.
    """
    url = BASE_URL + category
    data = requests.get(url).json()

    if category in data:
        return data[category]

    return data


if __name__ == '__main__':
    file_date = strftime('%Y%m%d')
    title_date = strftime('%Y %b %d')
    full_datetime = strftime('%Y %b %d %H:%M:%S %z')
    report_dir = Path('reports') / file_date

    if not report_dir.exists():
        report_dir.mkdir()

    # Write out the raw data and the pie charts
    for category in 'keyboards', 'locations':
        data = fetch_metrics(category)
        category_json = report_dir / f'{category}.json'
        json.dump(data, category_json.open('w'))

        if data:
            generate_pie_chart(data, f'{report_dir}/{category}.svg')

    # Write the report md
    index_md = f"""# QMK Statistics For {title_date}

This page shows usage of the QMK Configurator for the 24 hour period ending {full_datetime}.

# Keyboard Compiles

This chart shows all keyboards that were compiled today.

<img src="/reports/{file_date}/keyboards.svg">

# Locations

This chart shows where users using QMK Configurator came from today.

<img src="/reports/{file_date}/locations.svg">
    """
    (report_dir / 'index.md').write_text(index_md)

    # Update the sidebar
    sidebar = ["* Reports"]
    for dir in Path('reports').iterdir():
        if dir.is_dir:
            sidebar.append(f'    * [{dir}](/{dir}/index.md)')

    Path('_summary.md').write_text('\n'.join(sidebar))
