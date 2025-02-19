# Copyright 2024 AI in Medical Imaging, German Center for Neurodegenerative Diseases(DZNE), Bonn
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# IMPORTS
import numpy as np
from FastSurferCNN.data_loader.conform import getscale, scalecrop
import nibabel as nib
import sys
from HypVINN.config.hypvinn_global_var import hyposubseg_labels, SAG2FULL_MAP, HYPVINN_CLASS_NAMES, FS_CLASS_NAMES
##
# Helper Functions
##
def calculate_flip_orientation(iornt,base_ornt):
    # ornt[P, 1] is flip of axis N, where 1 means no flip and -1 means flip.
    new_iornt=iornt.copy()

    for axno, direction in np.asarray(base_ornt):
        idx=np.where(iornt[:,0] == axno)
        idirection=iornt[int(idx[0][0]),1]
        if direction == idirection:
            new_iornt[int(idx[0][0]), 1] = 1.0
        else:
            new_iornt[int(idx[0][0]), 1] = -1.0

    return new_iornt

# reorient image based on base image
def reorient_img(img,ref_img):
    '''
    orientation transform. ornt[N,1]` is flip of axis N of the array implied by `shape`, where 1 means no flip and -1 means flip.
    For example, if ``N==0 and ornt[0,1] == -1, and there’s an array arr of shape shape, the flip would correspond to the effect of
    np.flipud(arr). ornt[:,0] is the transpose that needs to be done to the implied array, as in arr.transpose(ornt[:,0])
    Parameters
    ----------
    img
    base_img

    Returns
    -------

    '''

    ref_ornt =nib.io_orientation(ref_img.affine)
    iornt=nib.io_orientation(img.affine)

    if not np.array_equal(iornt,ref_ornt):
        #flip orientation
        fornt = calculate_flip_orientation(iornt,ref_ornt)
        img = img.as_reoriented(fornt)
        #transpose axis
        tornt = np.ones_like(ref_ornt)
        tornt[:,0] = ref_ornt[:,0]
        img = img.as_reoriented(tornt)

    return img

# Transformation for mapping
def transform_axial2coronal(vol, axial2coronal=True):
    """
    Function to transform volume into coronal axis and back
    :param np.ndarray vol: image volume to transform
    :param bool axial2coronal: transform from axial to coronal = True (default),
                                transform from coronal to axial = False
    :return:
    """
    if axial2coronal:
        return np.moveaxis(vol, [0, 1, 2], [0, 2, 1])
    else:
        return np.moveaxis(vol, [0, 1, 2], [0, 2, 1])

def transform_axial2sagittal(vol, axial2sagittal=True):
    """
    Function to transform volume into Sagittal axis and back
    :param np.ndarray vol: image volume to transform
    :param bool coronal2sagittal: transform from coronal to sagittal = True (default),
                                transform from sagittal to coronal = False
    :return:
    """
    if axial2sagittal:
        return np.moveaxis(vol, [0, 1, 2], [2, 0, 1])
    else:
        return np.moveaxis(vol, [0, 1, 2], [1, 2, 0])


# Same as CerebNet.datasets.utils.rescale_image
def rescale_image(img_data):
    # Conform intensities
    src_min, scale = getscale(img_data, 0, 255)
    mapped_data = img_data
    if not img_data.dtype == np.dtype(np.uint8):
        if np.max(img_data) > 255:
            mapped_data = scalecrop(img_data, 0, 255, src_min, scale)

    new_data = np.uint8(np.rint(mapped_data))
    return new_data


# subseg: segmentation of subfield
def hypo_map_subseg2label(subseg):

    h, w, d = subseg.shape
    lbls, lbls_sag = hyposubseg_labels

    lut_subseg = np.zeros(max(lbls) + 1, dtype='int')
    for idx, value in enumerate(lbls):
        lut_subseg[value] = idx

    mapped_subseg = lut_subseg.ravel()[subseg.ravel()]
    mapped_subseg = mapped_subseg.reshape((h, w, d))


    # mapping left labels to right labels for sagittal view
    subseg[subseg == 2] = 1
    subseg[subseg == 5] = 4
    subseg[subseg == 6] = 3
    subseg[subseg == 8] = 7
    subseg[subseg == 12] = 11
    subseg[subseg == 20] = 13
    subseg[subseg == 24] = 23

    subseg[subseg == 126] = 226
    subseg[subseg == 127] = 227
    subseg[subseg == 128] = 228
    subseg[subseg == 129] = 229

    lut_subseg_sag = np.zeros(max(lbls_sag) + 1, dtype='int')
    for idx, value in enumerate(lbls_sag):
        lut_subseg_sag[value] = idx

    mapped_subseg_sag = lut_subseg_sag.ravel()[subseg.ravel()]

    mapped_subseg_sag = mapped_subseg_sag.reshape((h, w, d))

    return mapped_subseg,mapped_subseg_sag
def hypo_map_label2subseg(mapped_subseg):
    '''
       Function to perform look-up table mapping from label space to subseg space
    '''
    labels, _ = hyposubseg_labels
    subseg = np.zeros_like(mapped_subseg)
    h, w, d = subseg.shape
    subseg = labels[mapped_subseg.ravel()]

    return subseg.reshape((h, w, d))

def hypo_map_prediction_sagittal2full(prediction_sag):
    """
    Function to remap the prediction on the sagittal network to full label space used by coronal and axial networks
    :param prediction_sag: sagittal prediction (labels)
    :param lbl_type: type of label
    :return: Remapped prediction
    """

    idx_list = list(SAG2FULL_MAP.values())
    prediction_full = prediction_sag[:, idx_list, :, :]
    return prediction_full


def hypo_map_subseg_2_fsseg(subseg,reverse=False):
    fsseg = np.zeros_like(subseg,dtype=np.int16)

    if not reverse:
        for value, name in HYPVINN_CLASS_NAMES.items():
            fsseg[subseg == value] = FS_CLASS_NAMES[name]
    else:
        reverse_hypvinn = dict(map(reversed, HYPVINN_CLASS_NAMES.items()))
        for name,value in FS_CLASS_NAMES.items():
            fsseg[subseg == value] = reverse_hypvinn[name]
    return fsseg

