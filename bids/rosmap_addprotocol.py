import os
import pandas
import json
import sys
import shutil
import numpy as np

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
check_every = 1000

if __name__ == "__main__":
    
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col-0)

    print('Adding ROSMAP protocol to acq- part of BIDS filename')
    for i,row in datlog.iterrows():
        if count % check_every == 0:
            print('working on %s of %s'%((count+1),len(ds)))
        pth = row.new_path
        prot = row.ScannerGroup + row.Protocol
        acq = pth.split('acq-')[-1].split('_')[0]
        npth = pth.replace('acq-%s'%acq,'acq-%s%s'%(prot,acq))
        datlog.loc[i,'new_path'] = npth
        if row.ext == 'json' and row.Category == 'fmap':
            with open(pth) as json_data:
                j = json.load(json_data)
            if 'IntendedFor' in j.keys():
                ipth = j['IntendedFor']
                if 'acq-' in ipth:
                    acq = ipth.split('acq-')[-1].split('_')[0]
                    inpth = ipth.replace('acq-%s'%acq,'acq-%s%s'%(prot,acq)) 
                    j['IntendedFor'] = inpth
                    with open(pth, 'w') as fp:
                       json.dump(j, fp,sort_keys=True, indent=4)
                    datlog.loc[i,'intendedfor'] = inpth
        os.rename(pth,npth)
        count+=1

    datlog.to_csv(datlog_pth,index=False)