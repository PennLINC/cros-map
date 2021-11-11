import os
import numpy as np
from glob import glob
from nilearn import input_data
from pennlinckit.utils import get_sge_task_id


deriv_dir = '/cbica/projects/rosmap_fmri/DERIVATIVES/XCP/' 
extension = 'MNI152NLin6Asym_desc-residual_smooth_res-2_bold.nii.gz'
atlas_pth = '/cbica/projects/rosmap_fmri/dropbox/100ROIs-17nw-MNI152-3mm.nii'
save_pth = '/cbica/projects/rosmap_fmri/DERIVATIVES/XCP/rosmap_atl'
divisions = 18


#### SCRIPT

# initialize masker (resample to image space)
masker = input_data.NiftiLabelsMasker(atlas_pth,resampling_target='data')


# find images
bolds = sorted(glob(os.path.join(deriv_dir,'sub-*/ses-*/func/*%s'%extension)))

# calculate chunk size
chunksize = int(len(bolds)/divisions)
remainder = len(bolds)%divisions

# get specific image indexes
i = get_sge_task_id()
base = i*chunksize
if i < divisions:
    end = base + (chunksize-1)
else:
    end = base + (remainder-1)

for x in range(base,end):
    bold = bolds[x]

    # get subject information
    fdir,fnm = os.path.split(bold)
    sub = fnm.split('_')[0]
    ses = fnm.split('_')[1]

    # extract timeseries
    ts = masker.fit_transform(bold)
    newfl = os.path.join(save_pth,'%s_%s'%(sub,ses))

    # save timeseries
    np.savez_compressed(newfl,ts)