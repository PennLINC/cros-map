import os
import glob
import shutil
import pandas

audit = 'production/xcp_fail_audit.csv'
clone_dir = '/cbica/projects/rosmap_fmri/clone/fmriprep_outputs/'
example_dir = '/cbica/projects/rosmap_fmri/example_for_azeez/'
logdir = '/cbica/projects/rosmap_fmri/production/xcp-multises/analysis/logs/'

####
df = pandas.read_csv(audit,index_col=0)

os.chdir(clone_dir)
for i,row in df.iterrows():
    print('====working on %s===='%i)
    sub = i.split('xcp')[1]
    zips = sorted(glob(os.path.join(clone_dir,'%s*.zip'%sub)))
    elog = sorted(glob(os.path.join(logdir,'%s*.e*'%i)))[-1]
    olog = sorted(glob(os.path.join(logdir,'%s*.o*'%i)))[-1]
    exdir = os.path.join(example_dir,sub)
    if not os.path.isdir(exdir):
        os.mkdir(exdir)
    for z in zips:
        os.system('datalad get %s'%os.path.split(z)[1])
        os.system('datalad unlock %s'%os.path.split(z)[1])
        os.system('unzip %s'%z)
    for fdir in ['fmriprep','freesurfer']:
        if os.path.isdir(os.path.join(exdir,fdir)):
            os.system('rm -rf %s'%os.path.join(clone_dir,fdir)) 
            continue
        os.rename(os.path.join(clone_dir,fdir),os.path.join(exdir,fdir))
    for logfile in [elog,olog]:
        shutil.copy2(logfile,exdir)
    fr = os.path.join(exdir,'FailReason__%s'%row['FailReason'])
    os.system('touch %s'%fr)
