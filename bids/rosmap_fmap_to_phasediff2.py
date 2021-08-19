import os
import pandas
import json
from glob import glob

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
audit_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb10_iter2_audit.csv'
acq_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb10_iter2_AcqGrouping.csv'
check_every = 1000
pthcol = 'newpath_rmb7_iter2'
echotimes = [0.00492,0.00738]

if __name__ == "__main__":
    os.chdir(bids_dir)
    df = pandas.read_csv(datlog_pth,index_col=0)
    aud = pandas.read_csv(audit_pth,index_col=0)
    acq = pandas.read_csv(acq_pth)
    ags = aud[aud.JakeAnnot=='TraitError']['AcqGroup'].unique()
    ds = acq[acq.AcqGroup.isin(ags)]
    
    print('creating new paths, adding TE2 and updating spreadsheet')
    to_rename = {}
    for i,row in ds.iterrows():
        fmaps = sorted(glob(os.path.join(bids_dir,'%s/ses-%s/fmap/*'%(row['subject'],row['session']))))
        if len(fmaps) == 0: print('no fmaps for',row['subject'],row['session'])
        targets = [x for x in fmaps if 'phase1' in x and 't2' not in x]
        jpth = [x for x in targets if 'json' in x][0]
        npth = [x for x in targets if 'nii' in x][0]
        # add TEs
        with open(jpth) as json_data:
            j = json.load(json_data)
        if j['EchoTime'] not in echotimes:
            print('echo time of %s found for index %s'%(j['EchoTime'],i))
            j['EchoTime2'] = j['EchoTime']
        else:
            j['EchoTime2'] = echotimes[1]
        j['EchoTime1'] = echotimes[0]
        j.pop('EchoTime')
        with open(jpth, 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)
        # renaming and updating spreadsheet
        fdf = df[(df.subdir==row['subject']) & \
                 (df.sesdir=='ses-%s'%int(row['session'])) &\
                 (df.Modality=='phase') & (df.Category=='fmap')
                ].sort_values('ext')
        newj = jpth.replace('phase1','phasediff')
        newn = npth.replace('phase1','phasediff')
        to_rename.update({jpth:newj})
        to_rename.update({npth:newn})
        df.loc[fdf.index[0],pthcol] = newj
        df.loc[fdf.index[1],pthcol] = newn

    print('renaming files')
    for src,dest in to_rename.items():
        os.rename(src,dest)

    print('saving')
    df.to_csv(datlog_pth)
