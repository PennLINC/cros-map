#from glob import glob
from pennlinckit.utils import submit_array_job

#bolds = sorted(glob(os.path.join(deriv_dir,'sub-*/ses-*/func/*%s'%extension)))
divisions = 18
#chunksize = int(len(bolds)/divisions)
#remainder = len(bolds)%divisions

#for i in range(1,len(bolds)+1,chunksize):
#    first_sub=i
#    last_sub = i+chunksize-1

first_subset=1
last_subset = divisions+2
submit_array_job('/cbica/projects/rosmap_fmri/git/cros-map/derivatives/extract_fmri_data.py',first_subset,last_subset,RAM=16)
