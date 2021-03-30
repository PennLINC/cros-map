import os
import pandas
#import json
import sys
#import shutil
import numpy as np
import json 
from glob import glob
#sys.path.insert(0,'./')
#from rosmap_bidsify import update_log

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'

#path to validation output
val_pth = '/cbica/projects/rosmap_fmri/rosmap/rmb2_validation.csv'

#errlog_pth =  '/cbica/projects/rosmap_fmri/rosmap/BIDS_error_log.csv'
check_every = 1000


if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth)
    valdf = pandas.read_csv(val_pth)

    print('fixing non EPI IntendedFors')
    pths = valdf[valdf.type=='INTENDED_FOR'].files.values
    jpths = ['%s.json'%x.split('.')[0][1:] for x in pths]
    for i,jpth in enumerate(jpths):
        if i % check_every == 0:
            print('working on %s of %s'%(i,len(jpths)))
        with open(jpth) as json_data:
            j = json.load(json_data)
        intfor = j['IntendedFor']
        if intfor[-5:] == '.json':
            nif = intfor.replace('json','.nii.gz')
        else:
            match = datlog[datlog.new_path==pths[i][1:]].iloc[0]
            if not pandas.notnull(match['intendedfor']) and match['Modality'] !='epi':
                fpth = match['BIDS_dir'].replace('fmap','func')
                fimgs = sorted(glob(os.path.join(fpth,'*.nii.gz')))
                if len(fimgs) == 1:
                    fimg = fimgs[0]
                    #datlog.loc[i,'intendedfor'] = fimg
                    nif = 'ses'+ fimg.split('/ses')[1]
                else:
                    nif = ''
            elif match['Modality'] == epi:
                nif = ''
        j['IntendedFor'] = nif
        with open(jpth, 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)
    
    datlog.to_csv(datlog_pth) 

    print('adding RosmapProtocol to jsons')
    count = 0
    ds = datlog[datlog.ext=='json']
    for i,row in ds.iterrows():
        if count % check_every == 0:
            print('working on %s of %s'%(count,len(ds)))
        jpth = row['new_path']
        prot = '%s_%s'%(row['ScannerGroup'],row['Protocol'])
        with open(jpth) as json_data:
            j = json.load(json_data)
        j['RosmapProtocol'] = prot
        with open(jpth, 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)
        count += 1
