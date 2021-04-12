import os
import pandas
import json
import sys
import shutil
import numpy as np
import nibabel as nib
sys.path.insert(0,'./')
from rosmap_postvalidation3_nii import reorient_and_qform2sform, set_xyzt_units

datadir = '/cbica/projects/rosmap_fmri/rosmap/sourcedata/bnk_fmri/'
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
tmpdir = '/cbica/projects/rosmap_fmri/tmp/'
check_every = 20

def locate_datlog_index(fpath,datlog):
    hd = '/cbica/projects/rosmap_fmri/rosmap/sourcedata/data/raw/BNK/090211/'
    flnm = os.path.split(fpath)[-1].split('_fmri.')[0]
    fullpth = os.path.join(os.path.join(hd,flnm),'rfMRI.zip')
    if fullpth not in datlog.index:
        raise ValueError('Couldnt find %s in the datlog index'%fullpth)

    return fullpth

def convert_zipped_fmri(fpath, tmp_dir, outfile):
        
    # extract and concatenate
    with zipfile.ZipFile(fpath, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    fls = sorted(glob(os.path.join(tmp_dir,'*.img')))
    img = nib.concat_images(fls,check_affines=False,axis=3)
    
    # save image
    img.to_filename(outfile)

    # clean up
    for fl in fls:
        hdr = fl.split('.')[0]+'.hdr'
        os.remove(fl)
        os.remove(hdr)

    return outfile

def write_bnk_json(pth,base_json):
    with open(pth, 'w') as fp:
        json.dump(base_json, fp,sort_keys=True, indent=4)


if __name__ == "__main__":
    
    os.chdir(datadir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    fmris = sorted(glob(os.path.join(datadir,'*')))
    print('unzipping, renaming and prepping nii')

    for i, fmri in enumerate(fmris):
        if i % check_every == 0:
            print('working on %s of %s'%((i+1),len(fmris)))
        # find index in datlog
        dl_ind = locate_datlog_index(fmri, datlog)
        # get correct BIDS path for later
        dest,fnm = os.path.split(datlog.loc[dl_ind,'new_path'])
        # convert from .zip to nii
        nii = os.path.join(datadir,fnm)
        nii = convert_zipped_fmri(fmri,tmpdir,nii)
        # fix nii
        reoriented, error, message = reorient_and_qform2sform(nii)
        if error:
            raise ValueError(message)
        reoriented = set_xyzt_units(reoriented, xyz='mm', t='sec')
        os.remove(nii)
        reoriented.to_filename(nii)

        # get rid of old files
        os.remove(fmri)

