import os
import pandas
import json

datadir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
pathcol = 'newpath_rmb7_iter2'
check_every = 100

echotimes = [0.00492,0.00738]

#### script
os.chdir(datadir)
datlog = pandas.read_csv(datlog_pth,index_col=0)

# screen
print('identifying fieldmaps to update')
ch_inds = []
for bdir in datlog.BIDS_dir.unique():
    sdf = datlog[datlog.BIDS_dir==bdir]
    if sdf.ScannerGroup.values[0]!='MG': continue
    if 'phase' not in sdf.Modality.value_counts(): continue
    if sdf.Modality.value_counts()['phase'] == 2:
        ch_inds += sdf[sdf.Modality=='phase'].index.tolist()

print('adding second echotimes')
nm_changes = {}
count = 0
for i,row in ds.iterrows():
    if count % check_every == 0:
        print('working on %s of %s'%((count+1),len(ds)))
    old_pth = row[pathcol]
    new_pth = old_pth.replace('phase1.','phasediff.')
    # store name change to run at the end
    nm_changes.update({old_pth: new_pth})
    # save new path to spreadsheet
    datlog.loc[i,pathcol] = new_path
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
    count += 1

print('renaming images')
# rename images (doing this last because it's hardest to undo)
for oldpth,newpth in nm_changes.items():
    os.rename(oldpth,newpth)