#!/usr/bin/env python3

import os, json, itertools, math

import matplotlib
import matplotlib.pyplot as plt

import numpy

import grg_grgdata
from grg_grgdata.common import is_abstract
from grg_grgdata.common import min_value
from grg_grgdata.common import max_value

#nesta_dir = '../grg-nesta/opf'
nesta_dir = '../grg-nesta-plus'


def main():
    file_names = find_files()

    trans_tap_val_lookup = {}
    trans_shift_val_lookup = {}

    vm_min_lookup = {}
    vm_max_lookup = {}

    line_xr_ratio_lookup = {}
    trans_xr_ratio_lookup = {}

    line_xb_ratio_lookup = {}

    gen_ar_ratio_lookup = {}

    count = 0
    for file_name in file_names:
        with open(file_name, 'r') as file:
            data = json.load(file)
        # too slow for dev
        #grg_grgdata.cmd.validate_grg(data)
        print('passed: {}'.format(file_name))

        tap_val, shift_val = get_tap_bounds(data)
        trans_tap_val_lookup[file_name] = tap_val
        trans_shift_val_lookup[file_name] = shift_val

        vm_min, vm_max = get_voltage_bounds(data)
        vm_min_lookup[file_name] = vm_min
        vm_max_lookup[file_name] = vm_max

        line_xr_ratio, trans_xr_ratio = get_xr_ratios(data)
        line_xr_ratio_lookup[file_name] = line_xr_ratio
        trans_xr_ratio_lookup[file_name] = trans_xr_ratio

        line_xb_ratio_lookup[file_name] = get_xb_ratio(data)

        gen_ar_ratio_lookup[file_name] = get_ar_ratio(data)

        #if count > 3:
        #    break
        count += 1

    plot_hist([i for i in itertools.chain.from_iterable(trans_tap_val_lookup.values())], xlabel='Tap Ratio (p.u.)', file_name='tap.pdf')
    plot_hist([i for i in itertools.chain.from_iterable(trans_shift_val_lookup.values())], xlabel='Angle Shift (rad.)', file_name='shift.pdf')

    plot_hist([i for i in itertools.chain.from_iterable(vm_min_lookup.values())], xlabel='Voltage LB', file_name='vm_min.pdf')
    plot_hist([i for i in itertools.chain.from_iterable(vm_max_lookup.values())], xlabel='Voltage UB', file_name='vm_max.pdf')

    plot_hist([i for i in itertools.chain.from_iterable(line_xr_ratio_lookup.values())], xlabel='x/r ratio', file_name='line_xr_ratio.pdf')
    plot_hist([i for i in itertools.chain.from_iterable(trans_xr_ratio_lookup.values())], xlabel='x/r ratio', file_name='trans_xr_ratio.pdf')

    plot_hist([i for i in itertools.chain.from_iterable(line_xb_ratio_lookup.values())], xlabel='x/b ratio', file_name='line_xb_ratio.pdf')

    plot_hist([i for i in itertools.chain.from_iterable(gen_ar_ratio_lookup.values())], xlabel='active/reactive ratio', file_name='gen_ar_ratio.pdf')

    #print(vm_min_lookup)



def get_voltage_bounds(grg_data):
    vm_min = []
    vm_max = []

    for comp_id, comp in grg_data['network']['components'].items():
        if comp['type'] == 'logical_bus':
            #print(comp_id)
            vm_min.append(min_value(comp['voltage']['magnitude']))
            vm_max.append(max_value(comp['voltage']['magnitude']))

    return vm_min, vm_max


def get_tap_bounds(grg_data):
    tap_val = []
    shift_val = []

    for comp_id, comp in grg_data['network']['components'].items():
        if comp['type'] == 'two_winding_transformer':
            assert(not is_abstract(comp['transform']['tap_ratio']))
            assert(not is_abstract(comp['transform']['angle_shift']))
            tap = float(comp['transform']['tap_ratio'])
            shift = float(comp['transform']['angle_shift'])

            if not math.isclose(tap, 1.0):
                tap_val.append(tap)

            if not math.isclose(shift, 0.0):
                shift_val.append(shift)

    return tap_val, shift_val


def get_xr_ratios(grg_data):
    line_xr_ratio = []
    trans_xr_ratio = []

    for comp_id, comp in grg_data['network']['components'].items():
        if comp['type'] == 'line':
            #print(comp_id)
            assert(not is_abstract(comp['impedance']['resistance']))
            assert(not is_abstract(comp['impedance']['reactance']))
            r = float(comp['impedance']['resistance'])
            x = float(comp['impedance']['reactance'])

            if not math.isclose(r,0.0) and not math.isclose(x,0.0):
                line_xr_ratio.append(abs(x/r))

    for comp_id, comp in grg_data['network']['components'].items():
        if comp['type'] == 'two_winding_transformer':
            #print(comp_id)
            assert(not is_abstract(comp['impedance']['resistance']))
            assert(not is_abstract(comp['impedance']['reactance']))
            r = float(comp['impedance']['resistance'])
            x = float(comp['impedance']['reactance'])

            if not math.isclose(r,0.0) and not math.isclose(x,0.0):
                trans_xr_ratio.append(abs(x/r))

    return line_xr_ratio, trans_xr_ratio


def get_xb_ratio(grg_data):
    line_xb_ratio = []

    for comp_id, comp in grg_data['network']['components'].items():
        if comp['type'] == 'line':
            #print(comp_id)
            assert(not is_abstract(comp['impedance']['reactance']))
            x = float(comp['impedance']['reactance'])

            b = 0.0
            if 'from_shunt' in comp:
                assert(not is_abstract(comp['from_shunt']['susceptance']))
                b += float(comp['from_shunt']['susceptance'])

            if 'to_shunt' in comp:
                assert(not is_abstract(comp['to_shunt']['susceptance']))
                b += float(comp['to_shunt']['susceptance'])

            if not math.isclose(x, 0.0) and not math.isclose(b, 0.0):
                line_xb_ratio.append(abs(x/b))

    return line_xb_ratio


def get_ar_ratio(grg_data):
    gen_ar_ratio = []

    for comp_id, comp in grg_data['network']['components'].items():
        if comp['type'] == 'generator':
            active_min = min_value(comp['output']['active'])
            active_max = max_value(comp['output']['active'])
            
            reactive_min = min_value(comp['output']['reactive'])
            reactive_max = max_value(comp['output']['reactive'])

            active_mag = max(abs(active_min), abs(active_max))
            reactive_mag = max(abs(reactive_min), abs(reactive_max))

            if not math.isclose(active_mag, 0.0) and not math.isclose(reactive_mag, 0.0):
                gen_ar_ratio.append(active_mag/reactive_mag)

    return gen_ar_ratio




def plot_hist(data, bins=20, xlabel='', file_name=None, core_plot=False):
    plt.hist(data, bins=bins)
    plt.xlabel(xlabel)
    plt.ylabel('Frequency')
    plt.title('Histogram of {}'.format(xlabel))

    if file_name == None:
        plt.show()
    else:
        plt.savefig(file_name)

    plt.clf()

    if not core_plot:
        q = numpy.percentile(data, [20.0, 80.0])
        core_data = [x for x in data if x >= q[0] and x <= q[1]]
        core_file = None
        if file_name != None:
            core_file = file_name.replace('.', '_core.')
        plot_hist(core_data, bins=bins, xlabel=xlabel+' (20%-80% quant.)', file_name=core_file, core_plot=True)






def find_files():
    files = [] 

    ## walking dir causes network replication 

    # for dir_name, subdir_list, file_list in os.walk(nesta_dir):
    #     # just an optimization, walking these is slow
    #     if '.git' in dir_name:
    #         continue
    #     #print('Found directory: %s' % dir_name)
    #     for file_name in file_list:
    #         if file_name.endswith('.json'):
    #             print('found on %s - %s' % (dir_name, file_name))
    #             files.append(os.path.join(dir_name, file_name))

    for file_name in os.listdir(nesta_dir):
        if file_name.endswith('.json'):
            files.append(os.path.join(nesta_dir, file_name))

    return files


if __name__ == '__main__':
    main()
