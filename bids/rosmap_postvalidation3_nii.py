import os
import pandas
#import json
import sys
#import shutil
import numpy as np
import nibabel as nb
sys.path.insert(0,'./')
from rosmap_bidsify import update_log

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
errlog_pth =  '/cbica/projects/rosmap_fmri/rosmap/BIDS_error_log.csv'
check_every = 100

def reorient_and_qform2sform(fname):
    '''
    BIDS validator was having trouble with information missing in the qform
    and sform. In reality, the qform info was present, but not the sform. 
    This code will copy the information over and populate the qform and
    sform such that they are "correct".

    this code lifted and lightly adapted from https://github.com/nipreps/niworkflows/blob/1adb83fa05824cd8ef14ef7da07254fab3a248c5/niworkflows/interfaces/images.py#L476'''

    error = False
    message = None

    orig_img = nb.load(fname)
    reoriented = nb.as_closest_canonical(orig_img)

    # Set target shape information (target is self in this case)
    target_zooms = orig_img.header.get_zooms()[:3]
    target_shape = np.array(orig_img.shape)[:3]
    target_span = target_shape * target_zooms

    zooms = np.array(reoriented.header.get_zooms()[:3])
    shape = np.array(reoriented.shape[:3])

    # Reconstruct transform from orig to reoriented image
    ornt_xfm = nb.orientations.inv_ornt_aff(
        nb.io_orientation(orig_img.affine), orig_img.shape
    )
    # Identity unless proven otherwise
    target_affine = reoriented.affine.copy()
    conform_xfm = np.eye(4)

    xyz_unit = reoriented.header.get_xyzt_units()[0]
    if xyz_unit == "unknown":
        # Common assumption; if we're wrong, unlikely to be the only thing that breaks
        xyz_unit = "mm"

    # Set a 0.05mm threshold to performing rescaling
    atol_gross = {"meter": 5e-5, "mm": 0.05, "micron": 50}[xyz_unit]
    # if 0.01 > difference > 0.001mm, freesurfer won't be able to merge the images
    atol_fine = {"meter": 1e-6, "mm": 0.001, "micron": 1}[xyz_unit]

    # Update zooms => Modify affine
    # Rescale => Resample to resized voxels
    # Resize => Resample to new image dimensions
    update_zooms = not np.allclose(zooms, target_zooms, atol=atol_fine, rtol=0)
    rescale = not np.allclose(zooms, target_zooms, atol=atol_gross, rtol=0)
    resize = not np.all(shape == target_shape)
    resample = rescale or resize
    if resample or update_zooms:
        # Use an affine with the corrected zooms, whether or not we resample
        if update_zooms:
            scale_factor = target_zooms / zooms
            target_affine[:3, :3] = reoriented.affine[:3, :3] @ np.diag(
                scale_factor
            )

        if resize:
            # The shift is applied after scaling.
            # Use a proportional shift to maintain relative position in dataset
            size_factor = target_span / (zooms * shape)
            # Use integer shifts to avoid unnecessary interpolation
            offset = (
                reoriented.affine[:3, 3] * size_factor - reoriented.affine[:3, 3]
            )
            target_affine[:3, 3] = reoriented.affine[:3, 3] + offset.astype(int)

        conform_xfm = np.linalg.inv(reoriented.affine) @ target_affine

        # Create new image
        data = reoriented.dataobj
        if resample:
            data = nli.resample_img(reoriented, target_affine, target_shape).dataobj
        reoriented = reoriented.__class__(data, target_affine, reoriented.header)

    #     out_name = fname

    transform = ornt_xfm.dot(conform_xfm)
    if not np.allclose(orig_img.affine.dot(transform), target_affine):
        message = "Original and target affines are not similar"
        print(message)
        error = True

    return reoriented, error, message


def set_xyzt_units(img, xyz='mm', t='sec'):
    '''Was getting an error about TR units not being correct in the image 
    header. Copied this code directly from Luke Chang's solution at
    https://neurostars.org/t/bids-validator-giving-error-for-tr/2538'''
    header = img.header.copy()
    header.set_xyzt_units(xyz=xyz, t=t)
    return img.__class__(img.get_fdata().copy(), img.affine, header) 

##### script

if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth)
    errlog = pandas.read_csv(errlog_pth,index_col=0)
    eli = errlog.index[-1]+1

    print('fixing issues with BNK bold headers and qform/sform')
    ds = datlog[(datlog.ScannerGroup=='BNK') & \
            (datlog.Modality=='bold') & \
            (datlog.ext!='json')
            ]
    count = 0
    for i,row in ds.iterrows():
        if count % check_every == 0:
            print('working on %s of %s'%(count,len(ds)))
        fpth = row['new_path']
        reoriented, error, message = reorient_and_qform2sform(fpth)
        reoriented = set_xyzt_units(reoriented, xyz='mm', t='sec')
        if error:
            print('WARNING: %s'%message)
            log_input = dict(zip(['path','error'],
                                 [row['new_path'],message]))
            errlog = update_log(errlog,eli,errlog_pth,log_input)
            eli+=1
            count += 1
            continue
        else:
            reoriented.to_filename(fpth)
            count += 1   
    errlog.to_csv(errlog_pth)
