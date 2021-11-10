import os
from glob import glob


qc_dir = '/gpfs/fs001/cbica/projects/rosmap_fmri/QC/fmriprep'
pths = sorted(glob(os.path.join(qc_dir,'*.zip')))
subids = list(set([os.path.split(x)[1].split('_f')[0] for x in pths]))
script = '/cbica/projects/rosmap_fmri/general_code/fs_euler_checker_and_plots_simplified.py'
for i,subid in enumerate(subids):
    print('='*10,'working on %s of %s'%((i+1),len(subids)),'='*10)
    os.system('python %s %s %s'%(script,subid,qc_dir))
