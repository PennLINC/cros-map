import pandas
import json
from dateutil.parser import parse

## user input
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
check_every = 100

# change T1 acqusitions to...?
# key = ScannerGroup, value = new acq
changes = {'MG': 'acq-mgmprage','UC':'acq-ucmprage',
           'BNK':'acq-irspgr','Unknown':'acq-unk'}

# string indicating date after which change instructions
# from eyes closed to eyes open
tc_date = '20160923'


## functions

def rename_files(datlog,indices,func,check_every=100,rename=True):
    # get old an new paths
    sdf = datlog.loc[indices]
    old_paths = sdf.new_path.values
    new_paths = epidf.new_path.apply(func).values
    # replace path in spreadsheet
    datlog.loc[indices,'new_path'] = new_paths
    # rename file on disk
    if rename:
        for i in range(len(old_paths)):
            if i % check_every == 0: 
                print('working on %s of %s'%(i,len(indices)))
            os.rename(old_paths[i],new_paths[i])
    
    return datlog

## script
if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)

    # remove task from epi
    print('removing task from non bold epi images')
    epi_indx = datlog[datlog.Modality=='epi'].index
    epi_func = lambda x: x.replace('task-rest_','')
    datlog = rename_files(datlog,epi_indx,epi_func,check_every)
    datlog.to_csv(datlog_pth)

    # remove "-", "()" from obl
    print('removing bad characters from obl images')
    o_indx = [x for x in datlog.index if 'Obl2-' in datlog.loc[x,'new_path']]
    o_func = lambda x: x.replace('Obl2-','Obl2').replace('(','').replace(')','')
    datlog = rename_files(datlog,o_indx,o_func,check_every)
    datlog.to_csv(datlog_pth)

    # phase to phase1
    print('fixing modality for phasemaps')
    ph_indx = datlog[datlog.Modality=='phase'].index
    ph_func = lambda x: x.replace('_phase.','_phase1.')
    datlog = rename_files(datlog,o_indx,o_func,check_every)
    datlog.to_csv(datlog_pth)

    # diversify t1 acq
    print('diversifying t1 acquision')
    for scanner, acq in changes.items():
        t1_indx = datlog[(datlog.Modality == 'T1w') & \
                         (datlog.ScannerGroup==scanner)
                        ].index
        t1_func = lambda x: x.replace('acq-t1w',acq)
        datlog = rename_files(datlog,t1_indx,t1_func,check_every)
    datlog.to_csv(datlog_pth)
        

    # Add TaskName and Instructions to bold jsons
    print('Adding TaskName and Instructions to bold jsons')
    ds = datlog[(datlog.Modality=='bold') & (datlog.ext=='json')]
    tc_date = parse(tc_date)
    for i,row in ds.iterrows():
        if i % check_every == 0: 
            print('working on %s of %s'%(i,len(ds)))
        scandate = parse(str(row['ScanDate']))
        if (tc_date - scandate).days > 0: # if before the date
            inst = 'Eyes closed'
        else:
            inst = 'Eyes open'
        with open(row['new_path']) as json_data:
            j = json.load(json_data)
        j['TaskName'] = 'rest'
        j['Instructions'] = inst
        with open(row['new_path'], 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)
    print('all done')