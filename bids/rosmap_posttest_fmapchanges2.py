import os
import pandas
from glob import glob
import json

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
audit_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb15_iter1_audit.csv'
acq_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb15_iter1_AcqGrouping.csv'
pthcol = 'newpath_rmb7_iter2'
echotimes = [0.00492,0.00738]

if __name__ == "__main__":
    os.chdir(bids_dir)
    df = pandas.read_csv(datlog_pth,index_col=0)
    aud = pandas.read_csv(audit_pth,index_col=0)
    acq = pandas.read_csv(acq_pth)
    err = 'fmapErr_phasediff'
    ags = aud[aud.AuditStatus==err]['AcqGroup'].unique()
    ds = acq[acq.AcqGroup.isin(ags)]
    for i,row in ds.iterrows():
        jpth = glob(os.path.join(bids_dir,'%s/ses-%s/fmap/*.phasediff.json'%(row.subject,row.session)))[0]
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

