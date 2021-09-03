import os
import sys
import shutil
import pandas
from glob import glob
from copy import copy
from dateutil.parser import parse
sys.path.insert(0,'./')
from rosmap_bidsify import get_basic_info, get_protocol, update_log

datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
# location of downloaded data
datadir = '/cbica/projects/rosmap_fmri/rosmap/sourcedata/t1/'
# where you want the data to go
move_to = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
pthcol = 'newpath_rmb7_iter2'
check_every = 1000

protocols = {'UC': ['ProtUnk','20120221','20140922','20150706',
                    '20151120','20160125','20201129'],
             'MG': ['ProtUnk','20120501','20150715','20160621',
                    '20160627','20201129'],
             'BNK': ['ProtUnk','20090211']}

if __name__ == "__main__":
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    print('finding paths')
    paths = [os.path.join(dp, f) for dp, dn, filenames in os.walk(datadir) for f in filenames]
    print('Found %s paths'%len(paths))

    #### First pass -- sorting and updating
    print('sorting existing from new and updating data log')
    to_reset_sess = []
    t1_inds = []
    to_rename = {}
    new_projid = []
    for i,pth in enumerate(paths):
        if i % check_every == 0: print('working on',(i+1),'of',len(paths))
        npth = pth.split(datadir)[-1]
        split = npth.split('/')
        error,message,scannerGp,scandate,visit,projid,t1 = get_basic_info(split,pth)
        if 'nii.gz' in pth:
            ext = 'nii.gz'
        elif '.json' in pth:
            ext = 'json'
        match = datlog[(datlog.projid==int(projid)) & (datlog.Visit==int(visit)) & (datlog.Modality=='T1w') & (datlog.ext==ext)]
        if len(match) > 1:
            raise IOError('too many matches!')
        elif len(match) == 1:
            if pandas.notnull(match[pthcol].values[0]):
                abs_path = os.path.join(move_to,match[pthcol].values[0])
                to_rename.update({pth:abs_path})
                t1_inds.append(match.index[0])
            else:
                match = []
        if len(match) == 0:
            update_ses = False
            if int(projid) not in datlog.projid.unique():
                new_projid.append(int(projid))
            else:
                if int(visit) not in datlog[datlog.projid==int(projid)].Visit.unique():
                    if int(projid) not in to_reset_sess:
                        to_reset_sess.append(int(projid))
                else: 
                    update_ses = True
            nind = datlog.sort_index().index[-1] + 1
            t1_inds.append(nind)
            if update_ses:
                ses = datlog[(datlog.projid==int(projid)) & (datlog.Visit==int(visit))].Session.values[0]
                log_input = dict(zip(['ScannerGroup','ScanDate','Visit','projid','Category','Modality','ext','Session'],
                                    [scannerGp,'20'+str(scandate),int(visit),int(projid),'anat','T1w',ext,ses]
                                    ))
            else:
                log_input = dict(zip(['ScannerGroup','ScanDate','Visit','projid','Category','Modality','ext'],
                                    [scannerGp,'20'+str(scandate),int(visit),int(projid),'anat','T1w',ext]
                                    ))
            datlog = update_log(datlog,nind,datlog_pth,log_input,save=False)
            error,message,protocol = get_protocol(scannerGp,scandate,protocols)
            log_input = dict(zip(['Protocol'],[protocol]))
            datlog = update_log(datlog,nind,datlog_pth,log_input,save=False)

        
    #### SECOND PASS: Updating the sessions to accomodate new visits

    ### On first pass, seems like nothing needed a rename.
    ### Meaning all the new scans are just more recent visits than I had...
    for projid in to_reset_sess + new_projid:
        sdf = datlog[datlog.projid==projid]
        sessions = sdf.Visit.unique().tolist()
        sess_map = dict(zip(sorted(sessions),range(len(sessions))))
        for i,row in sdf.iterrows():
            datlog.loc[i,'Session'] = sess_map[row['Visit']]
            oldsess = copy(row['sesdir'])
            datlog.loc[i,'sesdir'] = 'ses-%s'%int(sess_map[row['Visit']])
            if pandas.notnull(row[pthcol]):
                if row['sesdir'] != oldsess:
                    oldpth = copy(row[pthcol])
                    datlog.loc[i,pthcol] = row[pthcol].replace(oldsess,row['sesdir'])
                    abs_path = os.path.join(move_to,row[pthcol])
                    to_rename.update({oldpth: abs_path})

    ### Get new BIDS paths and filenames
    to_remove = []
    print('getting new bids paths and filenames')
    for i,ind in enumerate(t1_inds):
        if i % check_every == 0:
            print('working on',(i+1),'of',len(t1_inds))
        acqstr = os.path.split(paths[i])[1].split('.')[0].replace('_','')
        row = datlog.loc[ind]
        acq = '%s%s'%(row['Protocol'],acqstr)
        if pandas.isnull(row['subdir']):
            subdir = 'sub-%s'%int(row['projid'])
            sesdir = 'ses-%s'%int(row['Session'])
            BIDS_dir = os.path.join('%s/%s/%s/'%
                                    (subdir,sesdir,row['Category']))
        else:
            subdir = row['subdir']
            sesdir = row['sesdir']
            BIDS_dir = row['BIDS_dir']    
        ext = row['ext']
        new_fl = '%s_%s_acq-%s_T1w.%s'%(subdir,sesdir,acq,ext)
        BIDS_path = os.path.join(BIDS_dir,new_fl)
        oldpth = copy(row[pthcol])
        log_input = dict(zip(['subdir','sesdir','BIDS_dir',pthcol,'ext'],
                             [subdir,sesdir,BIDS_dir,BIDS_path,ext])) 
        datlog = update_log(datlog,ind,datlog_pth,log_input,save=False)
        abs_path = os.path.join(move_to,BIDS_path)
        if pandas.notnull(oldpth):
            oabs = os.path.join(move_to,oldpth)
            if abs_path != oabs:
                to_remove.append(oabs)
        to_rename.update({paths[i]: abs_path})

    ## remove old filenames that will be replaced
    print('removing, renaming and saving')

    for pth in to_remove:
        if os.path.exists(pth):
            os.remove(pth)

    ### rename everything
    for src,dest in to_rename.items():
        shutil.copyfile(src,dest)



    ### save
    datlog.to_csv(datlog_pth)