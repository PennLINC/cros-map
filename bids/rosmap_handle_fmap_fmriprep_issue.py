import os
import pandas
import json
from glob import glob

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'

if __name__ == "__main__":
    os.chdir(bids_dir)
    df = pandas.read_csv(datlog_pth)

    renames = {}
    count = 0
    print('adding in missing intendedFors and IDing new fmap names')
    for i,row in df.iterrows():
        if count % check_every == 0:
            print('working on %s of %s'%(count,len(df)))
        count += 1
        if row['Category'] == 'fmap' and row['ext'] == 'json':
            if os.path.isfile(row['new_path']):
                df[df.new_path==row.new_path.replace('json','nii.gz')].iloc[0]
                # add in missing intended for if missing and necessary
                with open(row['new_path']) as json_data:
                    j = json.load(json_data)
                if 'IntendedFor' not in list(j.keys()):
                    ndir = row.BIDS_dir.replace('fmap','func')
                    fls = sorted(glob(os.path.join('/cbica/projects/rosmap_fmri/rosmap/rawdata/%s/'%ndir,'*.ni*')))
                    if len(fls) != 1: continue
                    fpth = fls[0]
                    bpth = 'ses-'+fpth.split('/ses-')[-1]
                    j['IntendedFor'] = bpth
                    with open(row['new_path'], 'w') as fp:
                        json.dump(j, fp,sort_keys=True, indent=4)

                # change fmap name to get rid of acq differences

                acq = row.new_path.split('acq-')[1].split('_')[0]
                nj_path = row.new_path.replace(acq,j['RosmapProtocol'])
                df.loc[i,'new_path'] = nj_path
                ni_path = match.new_path.replace(acq,j['RosmapProtocol'])
                df.loc[match.name,'new_path'] = ni_path
                renames.update({row.new_path: nj_path})
                renames.update({match.new_path: ni_path})


    print('renaming files')
    for src,dest in renames.items():
        os.rename(src,dest)

    df.to_csv(datlog_pth,index=False)