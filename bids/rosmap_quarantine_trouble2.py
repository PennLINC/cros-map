import os
import sys
import pandas
import shutil
import json
from glob import glob
sys.path.insert(0,'./')
from rosmap_quarantine_trouble import move_run_directory, find_indices_for_quarantine, descend_and_check


bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'

#path to validation output
val_pth = '/cbica/projects/rosmap_fmri/rosmap/rmb_validation.csv'
#path superfolder with quarantined images
quar_dir = '/cbica/projects/rosmap_fmri/quarantine/'

check_every = 1000


if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth)
    valdf = pandas.read_csv(val_pth)

    print('quarantining jsons with missing images')
    to_q = valdf[valdf.type=='SIDECAR_WITHOUT_DATAFILE'].files.tolist()
    # get rid of leading slash
    to_q = [x[1:] for x in to_q]
    dest = os.path.join(quar_dir,'missing_image')
    for fl in to_q:
        if not os.path.isdir(dest):
            os.mkdir(dest)
        for fl in to_q:
            try:
                os.rename(fl,dest)
            except:
                print('couldnt move %s to %s'%(fl,dest))
                continue
        idx = datlog[datlog['new_path']==to_q[0]].index[0]
        datlog.loc[idx,'quarantine'] = 'Yes'


    print('moving files with missing jsons')
    pths = valdf[valdf.type=='TOTAL_READOUT_TIME_MUST_DEFINE'].files.values
    dest = os.path.join(quar_dir,'missing_json')
    for f in pths:
        shutil.move(f[1:],dest)
        idx = datlog[datlog.new_path==f[1:]].index[0]
        datlog.loc[idx,'quarantine'] = 'Yes'

    print('moving more files with missing jsons')
    pths = valdf[valdf.type=='ECHO_TIME_MUST_DEFINE'].files.values
    dest = os.path.join(quar_dir,'missing_json')
    for f in pths:
        shutil.move(f[1:],dest)
        idx = datlog[datlog.new_path==f[1:]].index[0]
        datlog.loc[idx,'quarantine'] = 'Yes'

    print('fix phase encoding direction')
    ds = datlog[(datlog.Modality=='epi') & (datlog.ext=='json')]
    for i,row in ds.iterrows():
        jpth = row['new_path']
        if 'AP' in jpth or 'PIA' in jpth:
            ped = 'j-'
        elif 'PA' in jpth or 'PIP' in jpth:
            ped = 'j'
        else:
            raise ValueError('couldnt discern direction from',jpth)
        with open(jpth) as json_data:
            j = json.load(json_data)
        j['PhaseEncodingDirection'] = ped
        with open(jpth, 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)

    datlog.to_csv(datlog_pth)
