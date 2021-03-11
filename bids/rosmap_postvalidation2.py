import os
import pandas
import json
import sys
import shutil
import numpy as np
import nibabel as nib
sys.path.insert(0,'./')
from rosmap_bidsify import update_log


bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
errlog_pth =  '/cbica/projects/rosmap_fmri/rosmap/BIDS_error_log.csv'
check_every = 100

# Water-Fat Shift for EPI images. Taken directly from protocol
wfs = 18.049

# base json for bnk
base_json = {'Modality': 'MR',
             'MagneticFieldStrength': 1.5,
             'Manufacturer': 'GE',
             'ManufacturersModelName': 'SIGNA_EXCITE',
             'InstitutionName': 'Bannockburn_Radiology_Center',
             'DeviceSerialNumber': '00000847GURNEEMR',
             'StationName': 'BRCMR',
             'PatientPosition': 'HFS',
             'SoftwareVersions': '11',
             'TaskName':'rest',
             'Instructions':'Eyes closed',
             'EchoTime': 0.0033,
             'RepetitionTime': 2,
             'FlipAngle': 85,
             'PulseSequenceType': '2D Spiral GRE Resting State fMRI',
             'SliceThickness':5,
            'SliceEncodingDirection':'k',
            'SequenceName':'sprlio',
            'SliceTiming':[0.0,0.08,0.16,0.24,0.32,0.4,0.48,0.56,0.64,0.72,0.8,0.88,0.96,1.04,1.12,1.2,1.28,1.36,1.44,1.52,1.6,1.68,1.76,1.84,1.92,2.0]
            }

### Functions
def T2_IntendedFor(row,datlog,write_data=True):
    match = datlog[(datlog.Modality=='FLAIR') &\
                   (datlog.subdir==row['subdir']) &\
                   (datlog.sesdir==row['sesdir']) &\
                   (datlog.ext=='json')]
    if len(match) != 1:
        error = True
        message = '%s matches found for %s'%(len(match),row['new_path'])
    else:
        mrow = match.iloc[0]
        subpath = 'ses'+mrow['new_path'].split('/ses')[1]
        if write_data:
            with open(row['new_path']) as json_data:
                j = json.load(json_data)
            j['IntendedFor'] = subpath
            with open(row['new_path'], 'w') as fp:
                json.dump(j, fp,sort_keys=True, indent=4)
        error = False
        message = None
        
    return error,message

def calculate_TotalReadoutTime(in_meta,wfs,scanner):
    '''
    This is for a philips EPI sequence.
    See https://support.brainvoyager.com/brainvoyager/functional-analysis-preparation/29-pre-processing/78-epi-distortion-correction-echo-spacing-and-bandwidth
    and https://github.com/PennBBL/qsiprep/blob/master/qsiprep/interfaces/fmap.py#L469
    '''
    if 'MagneticFieldStrength' in in_meta:
        fstrength = in_meta['MagneticFieldStrength']
    else:
        if scanner == 'BNK':
            fstrength = 1.5
        elif scanner in ['UC','MG']:
            fstrength = 3
        else:
            raise IOError('field strength indetectable')
    wfd_ppm = 3.4  # water-fat diff in ppm
    g_ratio_mhz_t = 42.57  # gyromagnetic ratio for proton (1H) in MHz/T
    wfs_hz = fstrength * wfd_ppm * g_ratio_mhz_t
    #etl = in_meta['EchoTrainLength']
    reconmat = in_meta['ReconMatrixPE']
    #ees = wfs / (wfs_hz * reconmat) # used to be etl
    #trt = ees * (reconmat - 1)
    trt = wfs / wfs_hz
    in_meta['WaterFatShift'] = wfs
    #in_meta['EffectiveEchoSpacing'] = ees
    in_meta['TotalReadoutTime'] = trt
    
    return in_meta

def _get_pe_index(meta):
    pe = meta['PhaseEncodingDirection']
    try:
        return {'i': 0, 'j': 1, 'k': 2}[pe[0]]
    except KeyError:
        raise RuntimeError('"%s" is an invalid PE string' % pe)

def fix_IntendedFors(json_pth,if_path):
    with open(json_pth) as json_data:
        j = json.load(json_data)
    j['IntendedFor'] = if_path
    with open(json_pth, 'w') as fp:
        json.dump(j, fp,sort_keys=True, indent=4)

def write_bnk_json(pth,base_json):
    with open(pth, 'w') as fp:
        json.dump(base_json, fp,sort_keys=True, indent=4)

##### script

if __name__ == "__main__":
    
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth)
    errlog = pandas.read_csv(errlog_pth,index_col=0)
    eli = errlog.index[-1]+1

    print('Moving FLAIR phases to anat and adding IntendedFors')
    ds = datlog[(datlog.Category=='anat') & (datlog.Modality=='phase')]
    count = 0
    for i,row in ds.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(ds)))
        # move out of anat/ and into fmap/
        bidsdir = row['BIDS_dir'].replace('/anat/','/fmap/')
        oldpth = row['new_path']
        npath = oldpth.replace('/anat/','/fmap/')
        # update data log
        datlog.loc[i,'BIDS_dir'] = bidsdir
        datlog.loc[i,'new_path'] = npath
        # move file (UNCOMMENT WHEN READY TO ROCK)
        os.rename(oldpth,npath)
        # add IntendedFor to json
        if row['ext'] == 'json':
            row = datlog.loc[i]
            error,message = T2_IntendedFor(row,datlog)
            if error:
                print('WARNING: %s'%message)
                log_input = dict(zip(['path','error'],
                                     [row['new_path'],message]))
                errlog = update_log(errlog,eli,errlog_pth,log_input)
                eli+=1
        count += 1  
    datlog.to_csv(datlog_pth) 
    errlog.to_csv(errlog_pth)

    print('Adding TotalReadoutTime to epi jsons')
    ds = datlog[(datlog.Modality=='epi') & (datlog.ext=='json')]
    count = 0
    for i,row in ds.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(ds)))
        # see if TotalReadoutTime is Missing
        with open(row['new_path']) as json_data:
            j = json.load(json_data)
        if "PhaseEncodingAxis" in j.keys():
            j['PhaseEncodingDirection'] = j['PhaseEncodingAxis']
        if 'TotalReadoutTime' not in j.keys():
            # calculate and add it
            j = calculate_TotalReadoutTime(j,wfs,row['ScannerGroup'])
            # write it
            # UNCOMMENT WHEN READY
            with open(row['new_path'], 'w') as fp:
               json.dump(j, fp,sort_keys=True, indent=4)
        count += 1

    print("fixing up other IntendedFors")
    ds = datlog[(datlog.Modality=='phase') & (datlog.ext=='json')]
    count = 0
    for i,row in ds.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(ds)))
        if 'grefieldmappinge2ph_phase1' in row['new_path']:
            intfor = row['intendedfor']
            if intfor == 'Unknown':
                count +=1 
                continue
            if pandas.notnull(intfor):
                match = datlog[datlog[datlog.columns[0]]==intfor.replace('json','nii.gz')]
                if len(match) != 1:
                    message = 'Found %s matches to intendedfor for %s'%(
                                                              len(match),
                                                            row['new_path'])
                    print('WARNING: %s'%message)
                    log_input = dict(zip(['path','error'],
                                     [row['new_path'],message]))
                    errlog = update_log(errlog,eli,errlog_pth,log_input)
                    eli+=1
                else:
                    if_path = 'ses'+match.iloc[0]['new_path'].split('/ses')[1]
                    if '.json' in if_path:
                        if_path = if_path.replace('.json','.nii.gz')
                    ## UNCOMMENT WHEN READY!    
                    fix_IntendedFors(row['new_path'],if_path)
        count += 1

    print("creating base jsons for bnk fmri images")
    ds = datlog[(datlog.ScannerGroup=='BNK') & \
                (datlog.Modality=='bold') & \
                (datlog.ext!='json')
                ]
    count = 0
    for i,row in ds.iterrows():
        if count % check_every == 0:
            print('working on %s of %s'%(count,len(ds)))
        fpth = row['new_path']
        jpth = fpth.split('.')[0]+'.json'
        write_bnk_json(jpth,base_json)
        # make row in log for new file
        nind = jpth
        for col in row.index:
            if col == 'new_path':
                datlog.loc[nind,col] = jpth
            elif col == 'ext':
                datlog.loc[nind,col] = 'json'
            elif col == 'has_sidecar':
                datlog.loc[nind,col] = np.nan
            else:
                datlog.loc[nind,col] = row[col]
        datlog.loc[nind,'manually_created'] = 'Yes'
        # acknowledge that sidecar is now created
        datlog.loc[i,'has_sidecar'] = 'Yes'
        count += 1
    datlog.to_csv(datlog_pth)

