import pandas
import os
import shutil

datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
q_dir = '/cbica/projects/rosmap_fmri/quarantine/'
check_every = 100

if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    count = 0
    # get BNK images + jsons
    ds = datlog[(datlog.Modality=='bold') &\
                (datlog.ScannerGroup=='BNK') &\
                (datlog.ext!='json')]
    for ind,r in ds.iterrows():
        if count % check_every == 0:
            print('working on %s of %s'%(count,len(ds)))
        # id affiliated images
        matches = datlog[(datlog.projid==r['projid']) &\
                         (datlog.Session==r['Session'])]
        # make dirs
        for i,row in matches.iterrows():
            # make subdir
            tmp = os.path.join(q_dir,row['subdir'])
            if not os.path.isdir(tmp):
                os.mkdir(tmp)
            # make sesdir
            tmp = os.path.join(tmp,row['sesdir'])
            if not os.path.isdir(tmp):
                os.mkdir(tmp)
            # make filedir
            fdest = os.path.join(tmp,row['Category'])
            if not os.path.isdir(fdest):
                os.mkdir(fdest)
            # quarantine
            fpth = row['new_path']
            ####hd,flnm = os.path.split(fpth)
            shutil.move(fpth,fdest)
            #print('%s --> %s'%(fpth,fdest))
            datlog.loc[i,'quarantine'] = 'Yes'
        count += 1
    # finish up
     datlog.loc[datlog[datlog.quarantine!='Yes'].index,'quarantine'] = 'No'
     datlog.to_csv(datlog_pth)
