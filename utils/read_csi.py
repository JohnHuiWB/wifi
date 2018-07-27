#!/usr/bin/python
# -*- coding: utf-8 -*-

# @File  : read_csi.py
# @Author: JohnHuiWB
# @Date  : 2018/7/26 0026
# @Desc  :
# @Contact : huiwenbin199822@gmail.com
# @Software : PyCharm


import numpy as np


# skip 3 bytes
# 2 byte size field and 1 byte code
# always useless
skip_bytes = 3


def read_csi(path):
    """
    :param path: csi file path
    :return: data read from csi, have same structure with read_bf_file's.
    """
    with open(path, 'rb') as fp:
        origin_data = fp.read()

    data = []  # preprocessed data to return
    index = 0

    while index < len(origin_data):
        index += skip_bytes

        timestamp_low = origin_data[index] + (origin_data[index + 1] << 8) + (
            origin_data[index + 2] << 16) + (origin_data[index + 3] << 24)
        bfee_count = origin_data[index + 4] + (origin_data[index + 5] << 8)
        Nrx = origin_data[index + 8]
        Ntx = origin_data[index + 9]
        rssi_a = origin_data[index + 10]
        rssi_b = origin_data[index + 11]
        rssi_c = origin_data[index + 12]
        noise = origin_data[index + 13] - 256
        agc = origin_data[index + 14]
        antenna_sel = origin_data[index + 15]
        real_len = origin_data[index + 16] + (origin_data[index + 17] << 8)
        fake_rate_n_flags = origin_data[index +
                                        18] + (origin_data[index + 19] << 8)
        calc_len = (30 * (Nrx * Ntx * 8 * 2 + 3) + 7) // 8

        # Compute the permutation array
        permutation = [
            (antenna_sel & 0x3) + 1,
            ((antenna_sel >> 2) & 0x3) + 1,
            ((antenna_sel >> 4) & 0x3) + 1
        ]

        # Check that length matches what it should
        if calc_len != real_len:
            print('Wrong beamforming matrix size.')
            return None

        # Compute CSI from all this crap
        csi = np.zeros(shape=(Ntx, Nrx, 30), dtype=np.complex64)
        index += 20
        csi_index = 0
        for i in range(30):
            csi_index += 3  # skip 3, don't know why...
            remainder = csi_index % 8
            for j in range(Nrx * Ntx):
                real, imag = calc_csi(
                    origin_data[index + csi_index // 8],
                    origin_data[index + csi_index // 8 + 1],
                    origin_data[index + csi_index // 8 + 2],
                    remainder
                )
                csi[j // Nrx, j % Nrx, i] = complex(real, imag)
                csi_index += 16

        data.append([timestamp_low,
                     bfee_count,
                     Nrx,
                     Ntx,
                     rssi_a,
                     rssi_b,
                     rssi_c,
                     noise,
                     agc,
                     permutation,
                     fake_rate_n_flags,
                     csi])

        index += calc_len

    return data



def calc_csi(b1, b2, b3, remainder):
    """
    Function to calc binary number.
    This is not well supported by Python, so...
    :param b1:
    :param b2:
    :param b3:
    :param remainder:
    :return:
    """
    b1 = bin(b1).replace('0b', '')
    b1 = '0' * (8 - len(b1)) + b1
    b2 = bin(b2).replace('0b', '')
    b2 = '0' * (8 - len(b2)) + b2
    b3 = bin(b3).replace('0b', '')
    b3 = '0' * (8 - len(b3)) + b3

    r = int('0b' + b2[-remainder:] + b1[:8 - remainder], 2)
    i = int('0b' + b3[-remainder:] + b2[:8 - remainder], 2)

    if r > 127:
        r = r - 256
    if i > 127:
        i = i - 256

    return r, i


if __name__ == '__main__':
    print(len(read_csi(r'..\data\csi.dat')))
