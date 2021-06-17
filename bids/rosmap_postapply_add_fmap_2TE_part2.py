import os
import pandas
import json

datadir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
pathcol = 'newpath_rmb7_iter2'
valpth = '/cbica/projects/rosmap_fmri/rosmap/rmb8_validation.csv'

### code
os.chdir(datadir)
datlog = pandas.read_csv(datlog_pth,index_col=0)
valdf = pandas.read_csv(valpth)

scans = [x[1:] for x in valdf[valdf.type=='MISSING_MAGNITUDE1_FILE'].files]
print('fixing phasemap to phase1')
for scan in scans:
    match = datlog[datlog[pathcol]==scan].index[0]
    jpth = scan.replace('.nii.gz','.json')
    jmatch = datlog[datlog[pathcol]==jpth].index[0]
    newpth = scan.replace('phasediff','phase1')
    newjpth = jpth.replace('phasediff','phase1')
    with open(jpth) as json_data:
       j = json.load(json_data)
    j['EchoTime'] = j['EchoTime2']
    j.pop('EchoTime1')
    j.pop('EchoTime2')
    with open(jpth, 'w') as fp:
        json.dump(j, fp,sort_keys=True, indent=4)
    os.rename(scan,newpth)
    os.rename(jpth,newjpth)
    datlog.loc[match,pathcol] = newpth
    datlog.loc[jmatch,pathcol] = newjpth

print('converting phase1 to phasemap')
ds = datlog[(datlog.Category=='fmap') & (datlog.Protocol=='20150715')]
nm_changes = {}
for i,row in ds.iterrows():
    if 'phase1' not in row[pathcol]: continue
    old_pth = row[pathcol]
    new_pth = old_pth.replace('phase1.','phasediff.')
    nm_changes.update({old_pth: new_pth})
    # save new path to spreadsheet
    datlog.loc[i,pathcol] = new_pth
    # add double echotimes
    if row['ext'] == 'json':
        with open(old_pth) as json_data:
            j = json.load(json_data)
        if j['EchoTime'] not in echotimes:
            print('echo time of %s found for index %s'%(j['EchoTime'],i))
            j['EchoTime2'] = j['EchoTime']
        else:
            j['EchoTime2'] = echotimes[1]
        j['EchoTime1'] = echotimes[0]
        j.pop('EchoTime')
        with open(old_pth, 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)

print('renaming images')
# rename images (doing this last because it's hardest to undo)
for oldpth,newpth in nm_changes.items():
    os.rename(oldpth,newpth)

datlog.to_csv(datlog_pth)