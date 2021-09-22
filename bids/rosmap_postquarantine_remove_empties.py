import os
import pandas
from glob import glob

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
bv_path = '/cbica/projects/rosmap_fmri/rosmap/rmb18_validation.csv'

if __name__ == "__main__":
    os.chdir(bids_dir)
    bv = pandas.read_csv(bv_path)
    subs = bv[bv.type=='QUICK_VALIDATION_FAILED'].subject.values
    for sub in subs:
        subpth = os.path.join(bids_dir,sub)
        if os.path.isdir(subpth):
            os.remove(subpth)
