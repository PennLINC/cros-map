import os
import pandas
import shutil
from glob import glob

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'

#path to validation output
val_pth = '/cbica/projects/rosmap_fmri/rosmap/rmb_validation.csv'
#path superfolder with quarantined images
quar_dir = '/cbica/projects/rosmap_fmri/quarantine/'

check_every = 1000

def move_run_directory(source,dest,datlog,move_files=True, unlock=True):
   if not os.path.isdir(dest):
       os.mkdir(dest)
   sub,ses,mod,flnm = source.split('/')
   dsub = os.path.join(dest,sub)
   dses = os.path.join(dsub,ses)
   if not os.path.isdir(dsub):
       os.mkdir(dsub)
   parent_dir = os.path.split(os.path.split(source)[0])[0]
   q_index = find_indices_for_quarantine(parent_dir,datlog)
   if move_files:
        if unlock:
            ustr = os.path.join(parent_dir,'*/*')
            os.system('git annex unlock %s'%ustr)
        try:
            shutil.move(parent_dir,dsub)
        except:
            print('WARNING: could not move %s to %s'%(parent_dir,dsub))
    
   return dses, q_index

def find_indices_for_quarantine(parent_dir,datlog):
    sub,ses = parent_dir.split('/')
    q_index = datlog[(datlog.subdir==sub) & (datlog.sesdir==ses)].index
    return q_index

def descend_and_check(sudir):
    empties = []
    sesdirs = sorted(glob(os.path.join(subdir,'*')))
    if len(sesdirs) == 0:
        empties.append(subdir)
        return empties
    else:
        for sesdir in sesdirs:
            moddirs = sorted(glob(os.path.join(sesdir,'*')))
            if len(moddirs) == 0:
                empties.append(sesdir)
                continue
            else:
                for moddir in moddirs:
                    fls = sorted(glob(os.path.join(moddir,'*')))
                    if len(fls) == 0:
                        empties.append(moddir)
        return empties


if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth)
    valdf = pandas.read_csv(val_pth)
    print('preparing to clean up extraneous subjects')
    print('quarantining runs with missing phase jsons')
    to_q = valdf[valdf.type=='ECHO_TIME_MUST_DEFINE'].files.tolist()
    for fl in to_q:
        new_dir,q_index = move_run_directory(fl[1:],quar_dir,datlog)
        datlog.loc[q_index,'quarantine'] = 'Yes'


    print('quarantining jsons with missing images')
    to_q = valdf[valdf.type=='SIDECAR_WITHOUT_DATAFILE'].files.tolist()
    # get rid of leading slash
    to_q = [x[1:] for x in to_q]
    dest = os.path.join(quar_dir,'missing_image')
    for fl in to_q:
        if not os.path.isdir(dest):
            os.mkdir(dest)
        for fl in to_q:
            shutil.move(fl,dest)
        idx = datlog[datlog['new_path']==to_q[0]].index[0]
        datlog.loc[idx,'quarantine'] = 'Yes'

    print('quarantining subject with multidimension phase map')
    to_q = valdf[valdf.type=='MAGNITUDE_FILE_WITH_TOO_MANY_DIMENSIONS'].files.tolist()[0][1:]
    dest = os.path.join(quar_dir,'problem_subjects')
    new_dir, q_index = move_run_directory(to_q,dest,datlog)
    datlog.loc[q_index,'quarantine'] = 'Yes'
    txtfile = os.path.join(new_dir,'quarantine_note.txt' )
    with open(txtfile, 'w') as out_file:
        note = 'Phase images are cut off and multidimensional'
        out_file.write(note)

    print('removing empty subject directories')
    allsubs = sorted(glob('sub-*'))
    for i,subdir in enumerate(allsubs):
        if i % check_every == 0:
            print('working on %s of %s'%(i,len(allsubs)))
        empties = descend_and_check(subdir)
        if len(empties) > 0:
            print('the following directories for subject % were empty: %s'%(subdir,empties))
            print('deleting')
            for empty in empties:
                os.rmdir(empty)
