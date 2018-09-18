#!/usr/bin/env python3

import os, json, itertools, math, logging, sys

from io import StringIO

import grg_grgdata

#logger = logging.getLogger('grg')
#logger.setLevel(logging.DEBUG)

#print(logging.Logger.manager.loggerDict)
logger = logging.getLogger('grg_grgdata')
logger.propagate = False
#print(logger)

log_stream = StringIO()
log_handler = logging.StreamHandler(log_stream)
#logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

#nesta_dir = '../grg-nesta/opf'
#nesta_dir = '../grg-nesta-plus'
#nesta_dir = '../grg-grgdata/grg_grgdata/test/data/nesta'
#nesta_dir = '../grg-tamu-cases/grg'

nesta_dir = '../grg-pglib'

columns = [
    'bus',
    'shunt',
    'load',
    'generator',
    'synchronous_condenser',
    'ac_line',
    'two_winding_transformer'
]

def main():
    file_names = find_files()
    #file_names = [nesta_dir+'/nesta_case14_ieee.json', nesta_dir+'/nesta_case5_pjm.json']

    count = 0
    for file_name in file_names:
        log_stream.truncate(0)
        print('\nworking on: {}'.format(file_name))

        with open(file_name, 'r') as file:
            data = json.load(file)
        # too slow for dev
        #grg_grgdata.cmd.validate_grg(data)
        grg_grgdata.cmd.validate_grg_parameters(data)

        #print('')

        log_handler.flush()
        item_lookup = count_devices(data)
        warning_lookup = count_warnings(log_stream.getvalue())

        values = []
        for column in columns:
            items = item_lookup.get(column, 0)
            warns = warning_lookup[column]
            rate = round(100.0*warns/float(items) if items > 0 else 0, 1)
            if items > 0:
                print('{} - {}, {}'.format(column, items, rate))

        #print('')
        #print('passed: {}'.format(file_name))

        #if count > 3:
        #    break
        count += 1


def count_devices(data):
    counts = {}
    for k,v in grg_grgdata.cmd.walk_components(data):
        comp_type = v['type']
        if comp_type not in counts:
            counts[comp_type] = 0
        counts[comp_type] = counts[comp_type] + 1
    return counts


def count_warnings(string):
    #print(string)
    counts = {}
    counts['bus'] = string.count('bus_')
    #counts['shunt'] = string.count('shunt_')
    counts['load'] = string.count('load_')
    counts['generator'] = string.count('gen_')
    counts['synchronous_condenser'] = string.count('sync_cond_')
    counts['ac_line'] = string.count('line_')
    counts['two_winding_transformer'] = string.count('transformer_')

    # needed becouse of shunt warnings on lines
    counts['shunt'] = 0
    for line in string.split('\n'):
        if not 'line_' in line and 'shunt_' in line:
            counts['shunt'] = counts['shunt'] + 1

    messages = string.count('\n')
    if messages != sum(counts.values()):
        print(messages)
        print(counts)
    return counts


def find_files():
    files = [] 

    for file_name in os.listdir(nesta_dir):
        if file_name.endswith('.json'):
            files.append(os.path.join(nesta_dir, file_name))

    return files


if __name__ == '__main__':
    main()
