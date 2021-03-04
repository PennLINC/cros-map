import os
from glob import glob

quar_dir = '/cbica/projects/rosmap_fmri/quarantine/'
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'

dirs = sorted(glob('quarantine/*'))
for d in dirs:
    _,sub = os.path.split(d)
    if 'sub' not in sub: continue
    newdir = os.path.join(bids_dir,sub)
    shutil.move(d,new_dir)
    