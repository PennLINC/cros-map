import os
import pandas
import json

datadir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
pathcol = 'newpath_rmb7_iter2'

#### script
os.chdir(datadir)
datlog = pandas.read_csv(datlog_pth,index_col=0)
ds = datlog[(datlog.ScannerGroup=='BNK') & (datlog.Category=='fmap') & (datlog.ext=='json')]
for i,row in ds.iterrows():
    jpth = row[pathcol]
    with open(jpth) as json_data:
        j = json.load(json_data)
    if 'IntendedFor' in j.keys():
        j['IntendedFor'] = []
    with open(jpth, 'w') as fp:
       json.dump(j, fp,sort_keys=True, indent=4)
