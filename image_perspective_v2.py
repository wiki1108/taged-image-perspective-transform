#!/usr/bin/python2.7
# -*- coding:utf-8 -*-
__author__ = 'wiki'
__version__ = '2.0'
# 2.0 optimise perspective parameter to improve simulation effect
__date__ = '24/04/2018'

import sys

import cv2
import numpy as np
import os
import codecs
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString

def scan_img_data(data_dir):
    paths = []
    import os
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.jpg') and not file.startswith('.'):
                path = os.path.join(root, file)
                paths.append(path)
    return paths


def xml2obj(path):
    import xml.dom.minidom as minidom
    dom = minidom.parse(path)
    objects = dom.documentElement.getElementsByTagName('object')
    sizes = dom.documentElement.getElementsByTagName('size')
    path = path[:-4]
    data = {
        'path': path + '.jpg',
        'filename': path.split('/')[-1] + '.jpg',
        'labels': [],
        'region': [],
        'size': []
    }

    for size in sizes:
        width = size.getElementsByTagName("width")[0].firstChild.data
        height = size.getElementsByTagName("height")[0].firstChild.data
        data['size'] = [width, height]

    for obj in objects:
        brand = obj.getElementsByTagName("name")[0].firstChild.data
        box = obj.getElementsByTagName("bndbox")[0]
        xmin = int(box.getElementsByTagName("xmin")[0].firstChild.data)
        ymin = int(box.getElementsByTagName("ymin")[0].firstChild.data)
        xmax = int(box.getElementsByTagName("xmax")[0].firstChild.data)
        ymax = int(box.getElementsByTagName("ymax")[0].firstChild.data)
        data['labels'].append(brand)
        data['region'].append([xmin, ymin, xmax, ymax])
    return data


def scan_xml_data(data_dir):
    data = []
    import os
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.xml') and not file.startswith('.'):
                path = os.path.join(root, file)
                # print(path)
                obj = xml2obj(path)
                if os.path.isfile(obj['path']):
                    data.append(obj)
    return data


def zoom(xmin, ymin, xmax, ymax, zoom_scale):
    zoomed_box = []
    zoomed_box.append(0.5 * (xmax * (1 - zoom_scale) + xmin * (1 + zoom_scale)))  # zoomed xmin
    zoomed_box.append(0.5 * (ymax * (1 - zoom_scale) + ymin * (1 + zoom_scale)))  # zoomed ymin
    zoomed_box.append(0.5 * (xmax * (1 + zoom_scale) + xmin * (1 - zoom_scale)))  # zoomed xmax
    zoomed_box.append(0.5 * (ymax * (1 + zoom_scale) + ymin * (1 - zoom_scale)))  # zoomed ymax
    return zoomed_box


if __name__ == '__main__':
    First = True

    resized_width = 1280  # set this value to resize the output img with a fix width

    max_tran_scale = 7
    # transform scale can vary from 0 to 10. 0 is no transformation, 10 is maximum transformation.
    # Maximum transform value is the up limit of perspective scale.
    tran_nums = 5
    # number of transform scales within transform rate range
    tran_scales = np.linspace(1, max_tran_scale, num=tran_nums)

    zoom_scales = [0.05, 0.1, 0.3, 0.6, 1, 1.5 , 3, 5]  # 0.05, 0.1, 0.3, 0.6, 1.5 , 3, 5
    # Scales that the image will be zoomed

    sides = ['L', 'R', 'M']

    img_paths = scan_img_data('/Users/wikiwu/Desktop/continuous shooting image/front view')

    count = 0
    for image_path in img_paths:
        count += 1
        print('processing image %d of %d:' % (count, len(img_paths)), os.path.splitext(image_path)[0])

        SrcImg = cv2.imread(image_path)
        height, width, channels = SrcImg.shape

        resize_scale = resized_width / width

        min_box_size = max(30, resize_scale * height/50)
        # If either side of the transformed box is shorter than this value, it will be discarded.

        xml_path = os.path.splitext(image_path)[0] + '.xml'

        if os.path.isfile(xml_path):
            xml_data = xml2obj(xml_path)
            for region_num in range(len(xml_data['region'])):

                src_xmin = xml_data['region'][region_num][0]
                src_ymin = xml_data['region'][region_num][1]
                src_xmax = xml_data['region'][region_num][2]
                src_ymax = xml_data['region'][region_num][3]

                SrcPoints = np.float32([[src_xmin, src_ymin],
                                        [src_xmax, src_ymin],
                                        [src_xmin, src_ymax],
                                        [src_xmax, src_ymax]])

                xmin = 0.5 * (width - (src_xmax - src_xmin)) * resize_scale
                ymin = 0.5 * (height - (src_ymax - src_ymin)) * resize_scale
                xmax = 0.5 * (width + (src_xmax - src_xmin)) * resize_scale
                ymax = 0.5 * (height + (src_ymax - src_ymin)) * resize_scale
                # rearrange the bnd box to the center of the picture



                Img = SrcImg.copy()

                for zoom_scale in zoom_scales:
                    zoomed_box = zoom(xmin, ymin, xmax, ymax, zoom_scale)
                    zoomed_xmin = zoomed_box[0]
                    zoomed_ymin = zoomed_box[1]
                    zoomed_xmax = zoomed_box[2]
                    zoomed_ymax = zoomed_box[3]

                    for tran_scale in tran_scales:

                        for side in sides:

                            if side == 'L':
                                # fix left side
                                point_1 = [zoomed_xmin,
                                           zoomed_ymin]
                                point_2 = [zoomed_xmax - 0.05 * tran_scale * (zoomed_xmax - zoomed_xmin),
                                           zoomed_ymin + 0.04 * tran_scale * (zoomed_xmax - zoomed_xmin)]
                                point_3 = [zoomed_xmin,
                                           zoomed_ymax]
                                point_4 = [zoomed_xmax - 0.05 * tran_scale * (zoomed_xmax - zoomed_xmin),
                                           zoomed_ymax + 0.03 * tran_scale * (zoomed_xmax - zoomed_xmin)]

                            elif side == 'R':
                                # fix right side
                                point_1 = [zoomed_xmin + 0.05 * tran_scale * (zoomed_xmax - zoomed_xmin),
                                           zoomed_ymin + 0.04 * tran_scale * (zoomed_xmax - zoomed_xmin)]
                                point_2 = [zoomed_xmax,
                                           zoomed_ymin]
                                point_3 = [zoomed_xmin + 0.05 * tran_scale * (zoomed_xmax - zoomed_xmin),
                                           zoomed_ymax + 0.03 * tran_scale * (zoomed_xmax - zoomed_xmin)]
                                point_4 = [zoomed_xmax,
                                           zoomed_ymax]

                            else:
                                # no perspective transformation
                                point_1 = [zoomed_xmin, zoomed_ymin]
                                point_2 = [zoomed_xmax, zoomed_ymin]
                                point_3 = [zoomed_xmin, zoomed_ymax]
                                point_4 = [zoomed_xmax, zoomed_ymax]
                                tran_scale = 0

                            if min_box_size < (zoomed_xmax - zoomed_xmin) <= width * resize_scale \
                                    and min_box_size < (zoomed_ymax - zoomed_ymin) <= height * resize_scale:
                                # 20 is a setting minimum pixel to ensure sufficient image size for training.
                                # The image will info-less if this value is too small.

                                CanvasPoints = np.float32([[point_1[0], point_1[1]],
                                                           [point_2[0], point_2[1]],
                                                           [point_3[0], point_3[1]],
                                                           [point_4[0], point_4[1]]])

                                SrcPointsA = np.array(SrcPoints, dtype=np.float32)

                                CanvasPointsA = np.array(CanvasPoints, dtype=np.float32)

                                PerspectiveMatrix = cv2.getPerspectiveTransform(np.array(SrcPointsA),
                                                                                np.array(CanvasPointsA))
                                PerspectiveImg = cv2.warpPerspective(Img,
                                                                     PerspectiveMatrix,
                                                                     (int(width * resize_scale), int(height * resize_scale)))

                                output_path = os.path.splitext(image_path)[0] + '_%d_%s_%.2f_%.1f.jpg' % ((region_num + 1), side, zoom_scale, tran_scale)
                                cv2.imwrite(output_path, PerspectiveImg)

                                xml_xmin = min(point_1[0], point_2[0], point_3[0], point_4[0])
                                xml_xmax = max(point_1[0], point_2[0], point_3[0], point_4[0])
                                xml_ymin = min(point_1[1], point_2[1], point_3[1], point_4[1])
                                xml_ymax = max(point_1[1], point_2[1], point_3[1], point_4[1])

                                dict = {
                                    'filename': xml_data['filename'],
                                    'path': output_path,
                                    'source': {
                                        'database': 'Unknown'
                                    },
                                    'size': {
                                        'width': width,
                                        'height': height,
                                        'depth': channels
                                    },
                                    'segmented': 0,
                                    'object': {
                                        'name': xml_data['labels'][region_num],
                                        'pose': 'Unspecified',
                                        'truncated': 0,
                                        'difficult': 0,
                                        'bndbox': {
                                            'xmin': int(xml_xmin),
                                            'ymin': int(xml_ymin),
                                            'xmax': int(xml_xmax),
                                            'ymax': int(xml_ymax)
                                        }
                                    }
                                }
                                xml_content = dicttoxml(dict, custom_root='annotation', attr_type=False)
                                dom = parseString(xml_content)
                                xml_content = dom.toprettyxml()
                                output_path = os.path.splitext(image_path)[0] + '_%d_%s_%.2f_%.1f.xml' % (
                                    (region_num + 1), side, zoom_scale, tran_scale)
                                fo = codecs.open(output_path, "w", "utf-8")
                                fo.write(str(xml_content))
                                fo.close()
                            # else:
                            #     print('resized too small')
    print('finish')
