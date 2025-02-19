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

import os
from HypVINN.config.hypvinn_files import HYPVINN_LUT


def compute_stats(orig_path,prediction_path,save_dir,threads):
    from collections import namedtuple
    from FastSurferCNN.utils.checkpoint import FASTSURFER_ROOT
    from FastSurferCNN.segstats import main
    from HypVINN.config.hypvinn_files import HYPVINN_STATS_NAME
    from HypVINN.config.hypvinn_global_var import FS_CLASS_NAMES

    args = namedtuple('ArgNamespace', ['normfile', 'i', 'o', 'excludedid',
                                        'ids', 'merged_labels','robust',
                                        'threads','patch_size','device','lut','allow_root'])

    labels = list()

    for key,value in FS_CLASS_NAMES.items():
        if value !=0:
            labels.append(value)

    args.normfile = orig_path
    args.segfile = prediction_path
    args.segstatsfile = os.path.join(save_dir, HYPVINN_STATS_NAME)
    args.excludeid = [0]
    args.ids = labels
    args.merged_labels = []
    args.robust = None
    args.threads = threads
    args.patch_size = 32
    args.device = "auto"
    args.lut = os.path.join(FASTSURFER_ROOT,"FastSurferCNN", "config", "FreeSurferColorLUT.txt")
    args.allow_root = False
    flag = main(args)

    return flag




