import os
import sys
import json
import pandas
import numpy as np
from itertools import combinations
sys.path.insert(0,'./')
from rosmap_bidsify import update_log

#### User inputs
bids_dir = '/cbica/projects/rosmap_fmri/rosmap/bids/'
datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
errlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_error_log.csv'
check_every = 100

#### Control fields
mod_agn_fields = ['Manufacturer','ManufacturersModelName',
                 'DeviceSerialNumber','StationName',
                 'SoftwareVersions','MagneticFieldStrength',
                 'ReceiveCoilName','ReceiveCoilActiveElements',
                 'GradientSetType','MRTransmitCoilSequence',
                 'MatrixCoilMode','CoilCombinationMethod',
                 'CoilString','InstitutionName','InstitutionAddress',
                    'InstitutionalDepartmentName']

protocol_templates = {
    'T1w_BNK': {
        'PulseSequenceType': 'IR-FSPGR (RUN TWICE)',
        'ScanningSequence': 'SPGR',
        'ScanOptions': ['EDR','Fast','IrP'],
        'EchoTime': 0.0028,
        'RepetitionTime': 0.0063,
        'FlipAngle': 8,
        'PixelBandwidth': 31.25,
        'PercentPhaseFOV': 1,
        'SliceThickness': 1,
        'NumberShots':1,
        'DelayTime': 1,
        'Manufacturer': 'GE',
        'ManufacturersModelName': 'Signa',
        'MagneticFieldStrength': 1.5,
    },
    'T1w_UC': {
        'PulseSequenceType': 'MPRAGE',
        'RepetitionTime': 0.0081,
        'EchoTime': 0.0037,
        'ReceiveCoilName': 'SENSE-Head-8',
        'ReceiveCoilActiveElements': 'SENSE',
        'ParallelAcquisitionTechnique': 'SENSE',
        'FlipAngle': 8,
        'SliceEncodingDirection': 'j',
        'Manufacturer': "Philips",
        'ManufacturersModelName': 'Achieva Quasar TX',
        'SoftwareVersions': "R5.1.7",
        'MagneticFieldStrength': 3,
    },
    'T1w_MG': {
        'PulseSequenceType': 'MPRAGE',
        'RepetitionTime': 2.3,
        'EchoTime': 0.00298,
        'SliceThickness': 1,
        'SliceEncodingDirection': 'j',
        'NonlinearGradientCorrection': True,
        'ReceiveCoilActiveElements': 'HEA;HEP',
        'FlipAngle': 8,
        'MatrixCoilMode': 'Triple',
        'ParallelAcquisitionTechnique': 'GRAPPA',
        'ParallelReductionFactorInPlane': 2,
        'PixelBandwidth': 240,
        'EffectiveEchoSpacing': 0.0071,
        'Manufacturer': 'Siemens',
        'ManufacturersModelName': 'MAGNETOM TrioTim syngo MR B19',
        'MagneticFieldStrength': 3,
    },
    'BOLD_BNK': {
        'PulseSequenceType': '2D Spiral GRE Resting State fMRI',
        'SequenceName':'sprlio',
        'EchoTime': 0.0033,
        'RepetitionTime': 2,
        'FlipAngle': 85,
        'PixelBandwidth': 125,
        'SliceThickness': 5,
        'SliceEncodingDirection': 'k',
        'Manufacturer': 'GE',
        'ManufacturersModelName': 'Signa',
        'MagneticFieldStrength': 1.5,
    }
    
}

def build_protocol_base(datlog, mod_agn_fields):
    
    ds = datlog[datlog['has_sidecar']=='No']
    protocol_base = {}
    for prot in ds.Protocol.unique():
        pdf = datlog[(datlog.Protocol==prot) & (datlog.ext=='json')]
        if len(pdf)==0:
            continue
        else:
            prow = pdf.iloc[0]
            temp = {}
            with open(prow['new_path']) as json_data:
                j = json.load(json_data)
            for field in mod_agn_fields:
                if field in j.keys():
                    temp.update({field:j[field]})
            protocol_base.update({prot: temp})

    return protocol_base

def build_protocol_template(row,protocol_templates,protocol_base,mod_agn_fields):

    key = '%s_%s'%(row['Modality'],row['ScannerGroup'])
    if key not in protocol_templates.keys():
        temp = {'PhaseEncodingDirection':'k'}
    else:
        temp = protocol_templates[key]
        
    # update template with scan from same protocol
    if row['Protocol'] in protocol_base.keys():
        for k,v in protocol_base[row['Protocol']].items():
            if k in mod_agn_fields:
                temp[k] = v

    return temp

def fmap_handling(datlog,row):

    matches = datlog[(datlog.BIDS_dir==row['BIDS_dir']) &\
                         (datlog.ext=='json')]
        
    jsons = {}
    for ind,mrow in matches.iterrows():
        with open(mrow['new_path']) as json_data:
            j = json.load(json_data)
        jsons.update({ind: j})
    ufields = []
    mut_excl = []
    for a,b in combinations(matches.index.tolist(),2):
        mutexcl = set(jsons[a].keys()) ^ set(jsons[b].keys())
        ufields += list(mutexcl)
        mut_excl += list(mutexcl)
        union = list(set(jsons[a].keys()) & set(jsons[b].keys()))
        u = [x for x in union if jsons[a][x] != jsons[b][x]]
        ufields += u
    ufields = np.unique(ufields + mut_excl)
    with open(matches.iloc[0]['new_path']) as json_data:
        temp = json.load(json_data)
    for field in ufields:
        if field in mutexcl:
            entry = []
            for k,v in jsons.items():
                if field in v.keys():
                    entry.append(v[field])
                else:
                    entry.append('<MISSING>')
            temp.update({field: entry})
        else:
            new_field = [jsons[x][field] for x in jsons.keys()]
            temp.update({field: new_field})

    return temp


if __name__ == "__main__":

    # load stuff
    os.chdir(bids_dir)
    datlog = pandas.read_csv(datlog_pth,index_col=0)
    errlog = pandas.read_csv(errlog_pth,index_col=0)
    eli = errlog.index[-1]+1

    # build protocol base
    protocol_base = build_protocol_base(datlog,mod_agn_fields)

    # create jsons
    ds = datlog[datlog['has_sidecar']=='No']
    count=0
    for i,row in ds.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(ds)))
        if row['Category'] != 'fmap':
            temp = build_protocol_template(row,protocol_templates,protocol_base,mod_agn_fields)
        elif row['Category'] == 'fmap' and '_merged' in i:
            temp = fmap_handling(datlog,row)
        else:
            message = 'Did not account for this missing protocol'
            log_input = dict(zip(['path','error'],[i,message]))
            errlog = update_log(errlog,eli,errlog_pth,log_input)
            eli+=1
            count += 1
            continue
        # update log and save to disk
        split = row['new_path'].split('/')
        flnm = split[-1].split('.')[0]
        json_path = os.path.join(row['BIDS_dir'],'%s.json'%flnm)
        # make row in log for new file
        nind = json_path
        for col in row.index:
            if col == 'new_path':
                datlog.loc[nind,col] = json_path
            elif col == 'ext':
                datlog.loc[nind,col] = 'json'
            elif col == 'has_sidecar':
                datlog.loc[nind,col] = np.nan
            else:
                datlog.loc[nind,col] = row[col]
        # add new column for manual creation
        datlog.loc[nind,'manually_created'] = 'Yes'
        # acknowledge that sidecar is now created
        datlog.loc[i,'has_sidecar'] = 'Yes'
        # save json to disk
        with open(json_path, 'w') as fp:
            json.dump(temp, fp, sort_keys=True, indent=4)
        count += 1

    # fill in new column
    datlog[datlog.manually_created!='Yes']['manually_created'] = 'No'

    # save log
    datlog.to_csv(datlog_pth)
