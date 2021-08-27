import os
import pandas
import json
import numpy as np

bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
bv_path = '/cbica/projects/rosmap_fmri/rosmap/rmb12_validation.csv'
pthcol = 'newpath_rmb7_iter2'
check_every = 100
n_slices = 45 # obtained from protocol
slice_order = list(range(0,n_slices,2)) + list(range(1,n_slices,2)) # interleaved ascending
epi_factor = 59 # obtained from protocol

# some of these equations came from
# https://support.brainvoyager.com/brainvoyager/functional-analysis-preparation/29-pre-processing/78-epi-distortion-correction-echo-spacing-and-bandwidth

if __name__ == "__main__":
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    bv = pandas.read_csv(bv_path)
    print('adding slice timing, ees and task name to EPI jsons')
    for pth in pths:
        npth = os.path.join(bids_dir,pth[1:])
        jnk = datlog[datlog[pthcol]==pth[1:]]
        if len(jnk) == 0:
            jnk = datlog[datlog[pthcol]==npth]
        jrow = datlog[datlog[pthcol] == jnk[pthcol].values[0].replace('.nii.gz','.json')]
        jpth = jrow[pthcol].values[0]
        with open(jpth) as json_data:
            j = json.load(json_data)
        tr = j['RepetitionTime']
        times = np.linspace(0,tr,n_slices)
        slice_timing = times[slice_order]
        j['SliceTiming'] = slice_timing
        j['TaskName'] = 'rest'
        j['SliceEncodingDirection'] = 'k'
        wfs = j['WaterFatShift']
        if 'EchoTrainLength' not in j.keys():
            j['EchoTrainLength'] = epi_factor + 1
        etl = j['EchoTrainLength']
        ees = wfs / (wfs*etl)
        j['EffectiveEchoSpacing'] = ees
        with open(jpth, 'w') as fp:
            json.dump(j, fp,sort_keys=True, indent=4)

