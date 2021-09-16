import os
import pandas
from glob import glob

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
audit_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb15_iter1_audit.csv'
acq_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb15_iter1_AcqGrouping.csv'
pthcol = 'newpath_rmb7_iter2'
quarantine_dir = '/cbica/projects/rosmap_fmri/quarantine/IncompleteFMAP/'

if __name__ == "__main__":
    os.chdir(bids_dir)
    df = pandas.read_csv(datlog_pth,index_col=0)
    aud = pandas.read_csv(audit_pth,index_col=0)
    acq = pandas.read_csv(acq_pth)
    to_rename = {}

    err = 'fmapErr_phasediff'
    print('fixing errors for',err)
    ags = aud[aud.AuditStatus==err]['AcqGroup'].unique()
    ds = acq[acq.AcqGroup.isin(ags)]
    for i,row in ds.iterrows():
        sdir = glob(os.path.join(bids_dir,'%s/ses-%s/fmap/*.nii.gz'%(row.subject,row.session)))
        fmap = [x for x in sdir if 'phase1' in x and 't2' not in x][0]
        fjson = fmap.replace('.nii.gz','.json')
        fnm = fmap.split(bids_dir)[1]
        jfnm = fnm.replace('.nii.gz','.json')
        match = df[df[pthcol]==fnm].index[0]
        jmatch = df[df[pthcol]==jfnm].index[0]
        newfnm = fmap.replace('phase1','phasediff')
        newjfnm = fjson.replace('phase1','phasediff')
        to_rename.update({fmap:newfnm})
        to_rename.update({fjson:newjfnm})
        df.loc[match,pthcol] = newfnm.split(bids_dir)[1]
        df.loc[match,pthcol] = newjfnm.split(bids_dir)[1]

    err = 'fmapErr_mag1'
    print('fixing errors for',err)
    ags = aud[aud.AuditStatus==err]['AcqGroup'].unique()
    ds = acq[acq.AcqGroup.isin(ags)]
    to_makedir = []
    for i,row in ds.iterrows():
        segment = '%s/ses-%s/fmap/'%(row.subject,row.session)
        sdir = os.path.join(bids_dir,segment)
        matches = df[df.BIDS_dir==segment].index
        df.loc[matches,'quarantine'] = 'Yes'
        subdir = os.path.join(quarantine_dir,row.subject)
        sesdir = os.path.join(subdir,'ses-%s'%row.session)
        to_makedir += [subdir,sesdir]
        newdir = os.path.join(sesdir,'fmap/')
        to_rename.update({sdir: newdir})

    print('creating necessary directories')
    for d in to_makedir:
        if not os.path.isdir(d):
            os.mkdir(d)

    print('moving files around')
    for src,dest in to_rename.items():
        os.rename(src,dest)

    print('saving')
    df.to_csv(datlog_pth)
