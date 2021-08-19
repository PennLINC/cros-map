import os
import pandas
import json
from glob import glob
from copy import copy

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
ndim_pth = '/cbica/projects/rosmap_fmri/rosmap/ndimvol_scans.csv'
pthcol = 'newpath_rmb7_iter2'
check_every = 100

if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    ndim = pandas.read_csv(ndim_pth,index_col=0)
    # find all epis
    f_epis = ndim[(ndim['ndim']==4) & (ndim.modality=='epi')].index
    ds = datlog.loc[f_epis]
    # get new paths
    print('getting new paths and adding intended fors')
    to_rename = {}
    count = 0
    missing_json = []
    for i,row in ds.iterrows():
        # update spreadsheet
        if count % check_every == 0: 
            print('working on %s of %s'%((count+1),len(ds)))
        if not os.path.exists(row[pthcol]):
            print(row[pthcol],'does not seem to exist. Skipping')
            count += 1
            continue
        json_pth = row[pthcol].replace('nii.gz','json')
        jind = datlog[datlog[pthcol]==json_pth].index[0]
        bdir = copy(row['BIDS_dir']) 
        for ind in [i,jind]:
            datlog.loc[ind,'Category'] = 'func'
            datlog.loc[ind,'Modality'] = 'bold'
            datlog.loc[ind,'BIDS_dir'] = row['BIDS_dir'].replace('fmap','func')
        newpth = row[pthcol].replace('/fmap/','/func/'
                            ).replace('_dir-AP_epi','_bold')
        to_rename.update({row[pthcol]: newpth})
        datlog.loc[i,pthcol] = newpth
        njpth = datlog.loc[jind,pthcol].replace('/fmap/','/func/'
                            ).replace('_dir-AP_epi','_bold')
        to_rename.update({datlog.loc[jind,pthcol]: njpth})
        datlog.loc[jind,pthcol] = njpth
        # add intendedfors
        jsons = datlog[(datlog.BIDS_dir==row['BIDS_dir']) & \
                       (datlog.ext=='json')]
        if len(jsons) == 0:
            count+=1
            continue
        psplit = newpth.split('/')
        ifor = '%s/%s/%s'%(psplit[1],psplit[2],psplit[3])
        for x,jrow in jsons.iterrows():
            jpth = jrow[pthcol]
            if not os.path.isfile(jpth):
                count+=1
                print('could not find',jpth,'for editing')
                continue
            with open(jpth) as json_data:
                j = json.load(json_data)
            j['IntendedFor'] = ifor
            # with open(jpth, 'w') as fp:
            #     json.dump(j, fp,sort_keys=True, indent=4)
        count+=1

    print('renaming files')
    for src,dest in to_rename.items():
        os.rename(src,dest)

    print('saving')
    datlog.to_csv(datlog_pth)