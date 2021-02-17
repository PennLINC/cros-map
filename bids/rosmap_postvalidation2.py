import os
import pandas
import json
import sys
import shutil
import nibabel as nib
sys.path.insert(0,'./')
from rosmap_bidsify import update_log


bids_dir = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
errlog_pth =  '/cbica/projects/rosmap_fmri/rosmap/BIDS_error_log.csv'
check_every = 100

# path to validation output
val_pth = '/cbica/projects/rosmap/rawdata/rmb_validation.csv'
# path superfolder with quarantined images
quar_dir = '/cbica/projects/rosmap_fmri/quarantine/'

# Water-Fat Shift for EPI images. Taken directly from protocol
wfs = 18.049


### Functions
def T2_IntendedFor(row, write_data=True):
    match = datlog[(datlog.Modality=='FLAIR') &\
                   (datlog.subdir==row['subdir']) &\
                   (datlog.sesdir==row['sesdir']) &\
                   (datlog.ext==r'json')]
    if len(match) != 1:
        error = True
        message = '%s matches found for %s'%(len(match),row['new_path'])
    else:
        mrow = match.iloc[0]
        if write_data:
            with open(row['new_path']) as json_data:
                j = json.load(json_data)
            j['IntendedFor'] = mrow['new_path']
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
    in_meta['TotalReadoutTime'] = wfs
    
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

def move_run_directory(source,dest,move_files=True):
    if not os.path.isdir(dest):
        os.mkdir(dest)
    sub,ses,mod,flnm = source.split('/')
    dsub = os.path.join(dest,sub)
    dses = os.path.join(dsub,ses)
    if not os.path.isdir(dsub):
        os.mkdir(dsub)
    parent_dir = os.path.split(os.path.split(fl)[0])[0]
    if move_files:
        shutil.move(parent_dir,dsub)
    
    return dses

##### script

if __name__ == "__main__":
    
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)
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
        os.rename(oldpth,npth)
        # add IntendedFor to json
        if row['ext'] == 'json':
            error,message = T2_IntendedFor(row)
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
            #with open(row['new_path'], 'w') as fp:
            #    json.dump(j, fp,sort_keys=True, indent=4)
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
                    if_path = match.iloc[0]['new_path']
                    if '.json' in if_path:
                        if_path = if_path.replace('.json','.nii.gz')
                    ## UNCOMMENT WHEN READY!    
                    fix_IntendedFors(row['new_path'],if_path)
        count += 0

    valdf = pandas.read_csv(val_pth)
    print('preparing to clean up extraneous subjects')
    print('quarantining runs with missing phase jsons')
    to_q = valdf[valdf.type=='ECHO_TIME_MUST_DEFINE'].files.tolist()
    for fl in to_q:
        new_dir = move_run_directory(fl[1:],quar_dir)

    print('quarantining jsons with missing images')
    to_q = valdf[valdf.type=='SIDECAR_WITHOUT_DATAFILE'].files.tolist()
    # get rid of leading slash
    to_q = [x[1:] for x in to_q]
    dest = os.path.join(quar_dir,'missing_image')
    if not os.path.isdir(dest):
        os.mkdir(dest)
    for fl in to_q:
        shutil.move(fl,dest)
    print('quarantining subject with multidimension phase map')
    to_q = valdf[valdf.type=='MAGNITUDE_FILE_WITH_TOO_MANY_DIMENSIONS'].files.tolist([0][1:])
    dest = os.path.join(quar_dir,'problem_subjects')
    new_dir = move_run_directory(to_q,dest)
    txtfile = os.path.join(new_dir,'quarantine_note.txt' )
    with open(txtfile, 'w') as out_file:
        note = 'Phase images are cut off and multidimensional'
        out_file.write(note)

