import os
import shutil
import pandas

datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
datadir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
pthcol = 'newpath_rmb7_iter2'
bval_pth = '/cbica/projects/rosmap_fmri/rosmap/rmb14_validation.csv'

if __name__ == "__main__":
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    bd = pandas.read_csv(bval_pth)
    paths = bd[bd.type=='NOT_INCLUDED'].files.values

    to_rename = {}
    for pth in paths:
        match = datlog[datlog[pthcol]==pth[1:]]
        row = datlog.loc[match.index[0]]
        osess = row['BIDS_dir'].split('/')[1]
        nsess = row['sesdir']
        nbp = row['BIDS_dir'].replace(osess,nsess)
        opath = os.path.join(datadir,row[pthcol])
        npath = opath.replace('/%s/'%osess,'/%s/'%nsess)
        to_rename.update({opath: npath})
        datlog.loc[match.index[0],'BIDS_dir'] = nbp
        datlog.loc[match.index[0],pthcol] = row[pthcol].replace('/%s/'%osess,'/%s/'%nsess)

    for src,dest in to_rename.items():
        hd,tl = dest.split('rawdata/')
        hd += 'rawdata/'
        sub,ses,cat,fnm = tl.split('/')
        subdir = os.path.join(hd,sub)
        sesdir = os.path.join(subdir,ses)
        catdir = os.path.join(sesdir,cat)
        if not os.path.isdir(subdir):
            os.mkdir(subdir)
        if not os.path.isdir(sesdir):
            os.mkdir(sesdir)
        if not os.path.isdir(catdir):
            os.mkdir(catdir)
        os.rename(src,dest)

    datlog.to_csv(datlog_pth)