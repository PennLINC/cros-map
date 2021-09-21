import os
import pandas
from glob import glob

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
audit_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb17_iter1_audit.csv'
acq_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb17_iter1_AcqGrouping.csv'
pthcol = 'newpath_rmb7_iter2'
quarantine_dir = '/cbica/projects/rosmap_fmri/rosmap/unprocessedSubs_rawdata/'
errs = ['NoT1','NoBOLD','ImageFileError_T1']

if __name__ == "__main__":
    os.chdir(bids_dir)
    df = pandas.read_csv(datlog_pth,index_col=0)
    aud = pandas.read_csv(audit_pth,index_col=0)
    acq = pandas.read_csv(acq_pth)
    to_move = {}

    for err in errs:
        print('working on scans with error',err)
        ag = aud[aud.AuditStatus==err].AcqGroup.unique()
        ds = acq[acq.AcqGroup.isin(ag)]
        for i,row in ds.iterrows():
            pth = os.path.join(bids_dir, '%s/ses-%s'%(row.subject,row.session))
            newpth = os.path.join(quarantine_dir, '%s/ses-%s'%(row.subject,row.session))
            subdir = os.path.join(quarantine_dir,row.subject)
            if not os.path.isdir(subdir): os.mkdir(subdir)
            to_move.update({pth: newpth})
            matches = df[(df.subdir==row.subject) & (df.sesdir=='ses-%s'%row.session)].index
            if len(matches) != 0:
                df.loc[matches,'processed'] = 'No'

    print('moving')
    for src,dest in to_move.items():
        os.rename(src,dest)

    df.to_csv(datlog_pth)