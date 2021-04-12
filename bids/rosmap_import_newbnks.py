import os
from glob import glob
import pandas
import json
import shutil
import numpy as np
import nibabel as nib

datadir = '/cbica/projects/rosmap_fmri/rosmap/sourcedata/bnk_fmri/'
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'

os.chdir(datadir)
datlog = pandas.read_csv(datlog_pth,index_col=0)
fmris = sorted(glob(os.path.join(datadir,'*.nii.gz')))

for fmri in fmris:
    _,fnm = os.path.split(fmri)
    split = fnm.split('_')
    bidsdir = '%s/%s/func/'%(split[0],split[1])
    fullpth = os.path.join(bidsdir,fnm)
    if fullpth not in datlog.new_path.values:
        print('NO MATCH FOR %s'%fullpth)
    else:
        dest = os.path.join(bids_dir,fullpth)
        os.rename(fmri,dest)