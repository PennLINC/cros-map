import os
from glob import glob

quar_dir = '/cbica/projects/rosmap_fmri/quarantine/'
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'

dirs = sorted(glob(os.path.join(quar_dir,'*')))
for d in dirs:
    _,sub = os.path.split(d)
    if 'sub' not in sub: continue
    # find matches
    match = glob(os.path.join(bids_dir,sub))
    newdir = os.path.join(bids_dir,sub)
    if len(match) == 0:
        print('moving entire directory for %s'%sub)
        shutil.move(d,bids_dir)
    else:
        subdirs = sorted(glob(os.path.join(d,'*')))
        print('moving the following subdirectories into',sub)
        for sd in subdirs:
            print(sd)
            shutil.move(sd,new_dir)
