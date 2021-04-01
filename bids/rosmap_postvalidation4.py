import os
import json 
import pandas
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'

check_every = 100

val_pth = '/cbica/projects/rosmap_fmri/rosmap/rmb3_validation.csv'

if __name__ == "__main__":
    os.chdir(bids_dir)
    valdf = pandas.read_csv(val_pth)

    print('fixing the intendedfors where there were mistakes')
    fls = [x[1:] for x in valdf[valdf.type=='INTENDED_FOR'].files.unique()]
    for i,fl in enumerate(fls):
        if i % check_every == 0:
            print('working on %s of %s'%(i,len(fls)))
        jpth = fl.replace('.nii.gz','.json')
        with open(jpth) as json_data:
            j = json.load(json_data)
        intfor = j['IntendedFor']
        j['IntendedFor'] = intfor.replace('..nii','.nii')
        with open(jpth, 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)
            

