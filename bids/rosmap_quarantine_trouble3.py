import os
import sys
import pandas
import shutil
sys.path.insert(0,'./')
from rosmap_quarantine_trouble import move_run_directory

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'

#path to validation output
val_pth = '/cbica/projects/rosmap_fmri/rosmap/rmb2_validation.csv'
#path superfolder with quarantined images
quar_dir = '/cbica/projects/rosmap_fmri/quarantine/'


if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth)
    valdf = pandas.read_csv(val_pth)

    print('unlocking and moving subs w/o jsons')
    fls = [x[1:] for x in valdf[valdf.type=='ECHO_TIME_MUST_DEFINE'].files.unique()]
    target_dir = os.path.join(quar_dir,'missing_json')
    for fl in fls:
        os.system('git annex unlock %s'%fl)
        shutil.move(fl,target_dir)

    print('getting rid of jsons for which we have no images')
    fls = [x[1:] for x in bd[bd.type=='SIDECAR_WITHOUT_DATAFILE'].files.unique()]
    for fl in fls:
        os.remove(fl) # these files have already been quarantined

    print('quarantining subject with multidimension phase map')
    to_q = valdf[valdf.type=='MAGNITUDE_FILE_WITH_TOO_MANY_DIMENSIONS'].files.tolist()[0][1:]
    dest = os.path.join(quar_dir,'problem_subjects')
    new_dir, q_index = move_run_directory(to_q,dest,unlock-True)
    datlog.loc[q_index,'quarantine'] = 'Yes'
    txtfile = os.path.join(new_dir,'quarantine_note.txt' )
    with open(txtfile, 'w') as out_file:
        note = 'Phase images are cut off and multidimensional'
        out_file.write(note)