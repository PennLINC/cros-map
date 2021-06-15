import os
import pandas
import json
import shutil

#bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
pathcol = 'newpath_rmb7_iter2'
check_every = 100

#### script
os.chdir(datadir)
datlog = pandas.read_csv(datlog_pth,index_col=0)

print('Adding missing PhaseEncodingDirection fields to jsons')
ds = datlog[(datlog.Category=='fmap') & (datlog.Modality!='epi') & (datlog.ext=='json')]
for i,row in ds.iterrows():
    if count % check_every == 0:
        print('working on %s of %s'%((count+1),len(ds)))
    pth = row[pathcol]
    if not os.path.isfile(pth):
        continue
    with open(pth) as json_data:
        j = json.load(json_data)
    if 'PhaseEncodingDirection' not in j.keys() and 'PhaseEncodingAxis' in j.keys():
        j['PhaseEncodingDirection'] = j['PhaseEncodingAxis']
    with open(pth, 'w') as fp:
        json.dump(j, fp,sort_keys=True, indent=4)
        
