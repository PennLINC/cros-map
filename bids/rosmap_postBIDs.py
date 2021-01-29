import pandas
import json
import warnings
import sys
import os
import json
import zipfile
import numpy as np
import nibabel as nb
from glob import glob
from nilearn.image import concat_imgs
from difflib import get_close_matches
sys.path.insert(0,'./')
from rosmap_bidsify import update_log

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/bids/' #cd to this dir
tmpdir = '/cbica/projects/rosmap_fmri/bidstemp/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
errlog_pth =  '/cbica/projects/rosmap_fmri/rosmap/BIDS_error_log.csv'

f_unzip = True
find_missing_sidecars = True
add_intendedfors = True

def convert_zipped_fmri(datlog,tmp_dir,errlog,eli,el_fl,check_every=1000):

    old_fpaths = []

    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)
    warnings.filterwarnings("ignore", message="Affine is different across subjects.")
    warnings.filterwarnings("ignore", message="Casting data")

    zips = datlog[datlog.ext=='zip']
    count = 0
    for i,row in zips.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(zips)))
        # build new path
        flpth = row['new_path']
        if not os.path.exists(flpth):
            message = 'could not find file at path %s'%flpth
            print(message)
            log_input = dict(zip(['path','error'],[flpth,message]))
            errlog = update_log(errlog,eli,el_fl,log_input)
            eli+=1
            count += 1
            continue
        old_fpaths.append(flpth)
        split = flpth.split('.')
        if len(split) == 3:
            new_flnm = '%s.%s.nii.gz'%(split[0],split[1])
        elif len(split) == 2:
            new_flnm = '%s.nii.gz'%(split[0])
        else:
            raise IOError('too many .s in path')

        if os.path.exists(new_flnm):
            count += 1
            continue
        
        # extract and concatenate
        with zipfile.ZipFile(flpth, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
        fls = sorted(glob(os.path.join(tmp_dir,'*.img')))
        img = concat_imgs(fls,dtype=np.int16,auto_resample=True,)
        img = nb.Nifti1Image(img.get_fdata(),img.affine,img.header)
        
        # save and update datalog
        img.to_filename(new_flnm)
        datlog.loc[i,'new_path'] = new_flnm
        datlog.loc[i,'ext'] = 'nii.gz'

        # deal with affines?

        # clean up
        for fl in fls:
            hdr = fl.split('.')[0]+'.hdr'
            os.remove(fl)
            os.remove(hdr)

        count += 1

    # get rid of old files
    for pth in old_fpaths:
        os.remove(pth)

    return datlog, errlog, eli

def sidecar_survey(datlog,check_every=1000):   
    count = 0
    new_paths = datlog.new_path.values
    for i,row in datlog.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(datlog)))
        if row['ext'] == 'json':
            count+=1
            continue
        split = row['new_path'].split('.')
        json_pth = '%s.json'%split[0]
        if json_pth in new_paths:
            datlog.loc[i,'has_sidecar'] = 'Yes'
        else:
            datlog.loc[i,'has_sidecar'] = 'No'
        count+=1

    return datlog

## DEAL WITH ERRLOG! 
## EITHER LOAD IT, OR MAKE A NEW ONE!
def set_fmap_json_IntendedFors(datlog,errlog,eli,el_fl,check_every=1000):
    count = 0
    ds = datlog[(datlog.Modality=='BOLD') & (datlog.ext=='json')]
    for i,row in ds.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(ds)))
        # get and add fmri shim settings
        with open(row['new_path']) as json_data:
            j = json.load(json_data)
        if 'ShimSetting' not in j.keys():
            matches = get_close_matches('ShimSetting',j.keys())
            message = 'ShimSetting not found in json. Did you mean %s?'%matches
            log_input = dict(zip(['path','error'],[row['new_path'],message]))
            errlog = update_log(errlog,eli,el_fl,log_input)
            eli+=1
            continue
        fmri_shim = np.array(j['ShimSetting'])
        # get fmri path
        split = row['new_path'].split('/')
        flnm = split[-1].split('.')[-1]
        fmri_path = '%s/%s.nii.gz'%(split[1],flnm)
        
        # get and compare fieldmap shim settings
        fmap_pth = '%s/%s/fmap/'%(row['subdir'],row['sesdir'])
        sdf = datlog[(datlog.BIDS_dir==fmap_pth) & (datlog.ext=='json')]
        for fm,frow in sdf.iterrows():
            with open(frow['new_path']) as json_data:
                j = json.load(json_data)
            if 'ShimSetting' not in j.keys():
                matches = get_close_matches('ShimSetting',j.keys())
                message = 'ShimSetting not found in json. Did you mean %s?'%matches
                log_input = dict(zip(['path','error'],[fm,message]))
                errlog = update_log(errlog,eli,el_fl,log_input)
                eli+=1
                continue
            else:
                fmap_shim = np.array(j['ShimSetting'])
                shim_diff = abs(fmri_shim - fmap_shim).mean()
                # update spreadsheet and json file
                if all(np.isclose(fmap_shim,fmri_shim,atol=50)):
                    datlog.loc[fm,'intendedfor'] = i
                    datlog.loc[fm,'bold_shim_diff'] = shim_diff
                    j['IntendedFor'] = fmap_pth
                    with open(frow['new_path'], 'w') as fp:
                        json.dump(j, fp,sort_keys=True, indent=4)
                else:
                    datlog.loc[fm,'intendedfor'] = 'Unknown'
                    datlog.loc[fm,'bold_shim_diff'] = shim_diff
        count+=1

    return datlog, errlog, eli

if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    errlog = pandas.read_csv(errlog_pth,index_col=0)
    eli = errlog.index[-1]+1
    if f_unzip:
        print('converting fmri.zip files')
        datlog,errlog,eli = convert_zipped_fmri(datlog,tmpdir,errlog,eli,
                                                errlog_pth,check_every=50)
        print('saving progress...')
        datlog.to_csv(datlog_pth)

    if find_missing_sidecars:
        print('assessing sidecar coverage')
        datlog = sidecar_survey(datlog,check_every=1000)
        print('saving progress...')
        datlog.to_csv(datlog_pth)

    if add_intendedfors:
        print('adding IntendedFor fields to fieldmap sidecars')
        datlog,errlog,eli = set_fmap_json_IntendedFors(datlog,errlog,eli,
                                            errlog_pth,check_every=100)
        print('saving progress...')
        datlog.to_csv(datlog_pth)
        print('finished')
