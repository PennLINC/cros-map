import os
import shutil
import pandas
from glob import glob
from dateutil.parser import parse

##### USER INPUTS #####

# location of downloaded data
datadir = '/cbica/projects/rosmap_fmri/rosmap/sourcedata/data/raw/'

# where you want the data to go
move_to = '/cbica/projects/rosmap_fmri/rosmap/rawdata/'

# location of desired raw BIDS directory
#abs_path_prefix = '/cbica/projects/rosmap_fmri/rosmap/bids/' 

# mapping of unique search strings to BIDS categories and "modalities"
mapping = {'gre_field_mapping_e2_ph': ['fmap', 'phase'],
         'gre_field_mapping_e2': ['fmap', 'magnitude2'],
         'gre_field_mapping_e1': ['fmap', 'magnitude2'],
         'ep2d_fid_basic_bold': ['func', 'bold'],
         't2_fl3d_tra_No_SWI_ph': ['anat', 'phase'],
         't2_fl3d_tra_No_SWI': ['anat', 'FLAIR'],
         'gre_field_mapping_merged': ['discard', '?'],
         'EPI': ['fmap', 'epi'],
         'SE_EPI_P': ['fmap', 'epi'],
         'SE_EPI_A': ['fmap', 'epi'],
         'Obl_2-echo_GRE_(phase_map)_e1': ['fmap', 'phase'],
         'FieldMap': ['fmap', 'magnitude'],
         'FieldMap_ph': ['fmap', 'phase'],
         'SWI_ph': ['discard', 'phase'],
         'SWI_imaginary': ['discard', 'imaginary'],
         'SWI': ['discard', 'swi'],
         'SWI_real': ['discard', 'real'],
         'rfMRI': ['func', 'bold'],
         'Obl_2-echo_GRE_(phase_map)': ['fmap', 'phase'],
         'gre_field_mapping': ['fmap', 'magnitude'],
         'Obl_2-echo_GRE_(phase_map)_e1a': ['fmap', 'phase'],
         'Obl_2-echo_GRE_(phase_map)a': ['fmap', 'phase']}

# dict, keys=scanners, vals= list of dates where each new protocol began
protocols = {'UC': ['ProtUnk','20120221','20140922','20150706',
                    '20151120','20160125','20201129'],
             'MG': ['ProtUnk','20120501','20150715','20160621',
                    '20160627','20201129'],
             'BNK': ['ProtUnk','20090211']}

# filename (including desired path) of error and data logs
el_fl = '/cbica/projects/rosmap_fmri/rosmap/BIDS_error_log.csv'
dl_fl = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'

# For each phase of script, progress report every <check_every> iterations
check_every = 1000


##### FUNCTIONS #####

def get_basic_info(split,pth):
    # get scanner group, subid, ROSMAP visit and scan date
    acceptable = ['MG','BNK','UC']
    scannerGp = split[0]
    error = False
    if 't1' not in scannerGp:
        if scannerGp not in acceptable:
            message = 'SCANNER RECORDED AS %s. SKIPPING path %s'%(scannerGp,pth)
            error = True
        else:
            fnm = split[-1]
            substr = split[2]
            scandate, visit, projid = substr.split('_')
            #print(scannerGp,substr,fnm)
            t1 = False
    else:
        if '3t' in scannerGp:
                scannerGp = '3T'
        else:
            scannerGp = '1.5T'
        fnm = os.path.split(pth)[-1].split('.')[0]
        scandate, visit, projid = fnm.split('_')
        t1 = True
    
    if error:
        return error,message,None,None,None,None,None
    else:
        return error,None,scannerGp,scandate,visit,projid,t1 

def update_log(log,log_index,log_file,info,save=False):
    for field,data in info.items():
        log.loc[log_index,field] = data
    if save:
        log.to_csv(log_file)
    
    return log
    
def get_category_and_modality(split,t1,mapping):
# get category and modality
    error = False
    if t1:
        cat,modal = ('anat','T1w')
    else:
        filename = split[-1]
        found = False
        for key,info in mapping.items():
            if key in filename:
                cat,modal = info
                found = True
                break
        if not found:
            message = 'filename %s did not match any existing keys for path %s. SKIPPING!'%(
                          filename,npth)
            error = True
        if cat == 'discard':
            message = 'filename %s for path %smarked for discard by user'%(filename,npth)
            error = True

    if error:
        return error, message, None, None
    else:
        return error, None, cat, modal

# Get protocol
def get_protocol(scannerGp,scandate,protocols):
    dt = parse('20'+str(scandate))
    error = False
    if scannerGp not in protocols.keys():
        message = 'Scanner Group %s not included in protocol keys (%s)'%(scannerGp,protocols.keys())
        error=True
    found = False
    for i,prot in enumerate(protocols[scannerGp][1:]):
        if dt == parse(prot):
            protocol = prot
            found = True
            break
        i+=1
        if dt<parse(prot):
            protocol = protocols[scannerGp][(i-1)]
            found = True
            break
    if not found:
        if dt > parse(protocols[scannerGp][-1]):
            protocol = protocols[scannerGp][-1]
        else:
            protocol = 'ProtUnk'
    
    if error:
        return error, message, None
    else:
        return error, None, protocol

def get_file_parts(path,is_t1):
    hd,tl = os.path.split(path)
    exts = tl.split('.')
    tl = exts[0]
    if len(exts) == 3:
        ext = '%s.%s'%(exts[1],exts[2])
    else:
        ext = exts[-1]
    if is_t1:
        tl = 't1w'
    
    return hd,tl,ext

def get_BIDS_file_path(row, flnm, ext):
    if row['Category'] == 'func':
        new_fl = 'sub-%s_ses-%s_task-rest_acq-%s_%s.%s'%(
                                            row['projid'],int(row['Session']),
                                            flnm.replace('_',''),
                                            row['Modality'],ext) 
    elif row['Modality'] == 'epi':
        if 'EPI_P' in flnm:
            pdir = 'PA'
        elif 'EPI_A' in flnm:
            pdir = 'AP'
        else:
            pdir = 'AP'
        new_fl = 'sub-%s_ses-%s_task-rest_acq-%s_dir-%s_%s.%s'%(
                                            row['projid'],int(row['Session']),
                                            flnm.replace('_',''),pdir,
                                            row['Modality'],ext)

    else:
        new_fl = 'sub-%s_ses-%s_acq-%s_%s.%s'%(
                                    row['projid'],int(row['Session']),
                                    flnm.replace('_',''),
                                    row['Modality'],ext)
    return new_fl

# script
if __name__ == "__main__":

    print('FINDING PATHS')
    paths = [os.path.join(dp, f) for dp, dn, filenames in os.walk(datadir) for f in filenames]
    #(_, _, filenames) = next(os.walk(my_path))
    print('Found %s paths'%len(paths))
    
    errlog = pandas.DataFrame()
    eli = 0
    datlog = pandas.DataFrame()

    print('==============FIRST PASS: DATA LOGGING===============')

    for count,pth in enumerate(paths):
        if pth in datlog.index or pth in errlog.index:
            continue
        if count % check_every == 0:
            print('Working on path %s of %s'%(count+1,len(paths)))
        npth = pth.split(datadir)[-1]
        split = npth.split('/')
        error,message,scannerGp,scandate,visit,projid,t1 = get_basic_info(split,pth)
        if error:
            print(message)
            log_input = dict(zip(['path','error'],[pth,message]))
            errlog = update_log(errlog,eli,el_fl,log_input)
            eli+=1
            continue
        else:
            log_input = dict(zip(['ScannerGroup','ScanDate','Visit','projid'],
                                [scannerGp,'20'+str(scandate),visit,projid]
                                ))
            datlog = update_log(datlog,pth,dl_fl,log_input)

        error,message,cat,modal = get_category_and_modality(split,t1,mapping)
        if error:
            print(message)
            log_input = dict(zip(['path','error'],[pth,message]))
            errlog = update_log(errlog,eli,el_fl,log_input)
            eli+=1
            continue
        else:
            log_input = dict(zip(['Category','Modality'],[cat,modal]))
            datlog = update_log(datlog,pth,dl_fl,log_input)

        if not t1:
            error,message,protocol = get_protocol(scannerGp,scandate,protocols)
            if error:
                print(message)
                log_input = dict(zip(['path','error'],[pth,message]))
                errlog = update_log(errlog,eli,el_fl,log_input)
                eli+=1
            else:
                log_input = dict(zip(['Protocol'],[protocol]))
                datlog = update_log(datlog,pth,dl_fl,log_input)
    datlog.to_csv(dl_fl)
    errlog.to_csv(el_fl)

    print('==============SECOND PASS: GETTING T1 PROTOCOLS===============')
    no_match = []
    count = 0
    size = len(datlog[datlog.ScannerGroup.isin(['3T','1.5T'])])
    for i,row in datlog[datlog.ScannerGroup.isin(['3T','1.5T'])].iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,size))
        match = datlog[(datlog.projid==row['projid']) & \
                   (datlog.Visit==row['Visit']) & \
                   (datlog.Modality!='T1w')
                  ]
        if len(match) > 0:
            match=match.iloc[0]
    #         datlog.loc[i,'ScannerGroup'] = match['ScannerGroup']
    #         datlog.loc[i,'Protocol'] = match['Protocol']
            log_input = dict(zip(['ScannerGroup','Protocol'],
                                 [match['ScannerGroup'],match['Protocol']]))
            datlog = update_log(datlog,i,dl_fl,log_input)
        else:
            no_match.append(i)
            message = 'No matching session found for T1 file %s. Cant derive    scanner/protocol'%i
            print(message)
            log_input = dict(zip(['path','error'],[i,message]))
            errlog = update_log(errlog,eli,el_fl,log_input)
            eli+=1
            log_input = dict(zip(['ScannerGroup','Protocol'],
                                 ['Unknown','Unknown']))
            datlog = update_log(datlog,i,dl_fl,log_input)
        count+=1

# Round 3
    print('==============DERIVING SCAN SESSIONS===============')
    projids = datlog.projid.unique()
    for count,projid in enumerate(projids):
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(projids)))
        sdf = datlog[datlog.projid==projid]
        sessions = sdf.Visit.unique().tolist()
        sess_map = dict(zip(sorted(sessions),range(len(sessions))))
        for i,row in sdf.iterrows():
            datlog.loc[i,'Session'] = sess_map[row['Visit']]
    datlog.to_csv(dl_fl)

# Round 4
    abs_path_prefix = '' ##### NEEDS USER INPUT!!!    
    pool = []
    print('==============GENERATING PATHS===============')
    count = 0
    for i,row in datlog.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(datlog)))
        if row['Modality'] == 'T1w':
            t1=True
        else:
            t1=False
        hd,flnm,ext = get_file_parts(i,t1)
        subdir = 'sub-%s'%row['projid']
        sesdir = 'ses-%s'%int(row['Session'])
        BIDS_dir = os.path.join(abs_path_prefix,'%s/%s/%s/'%
                                (subdir,sesdir,row['Category']))
        new_fl = get_BIDS_file_path(row,flnm,ext)
        BIDS_path = os.path.join(BIDS_dir,new_fl)
        log_input = dict(zip(['subdir','sesdir','BIDS_dir','new_path','ext'],
                             [subdir,sesdir,BIDS_dir,BIDS_path,ext]))
        datlog = update_log(datlog,i,dl_fl,log_input,save=False)
        count+=1
    datlog.to_csv(dl_fl)

    print('==============MOVING FILES===============')
    count = 0
    for i,row in datlog.iterrows():
        if count % check_every == 0: 
            print('working on %s of %s'%(count,len(datlog)))
        subdir = os.path.join(move_to,row['subdir'])
        sesdir = os.path.join(subdir,row['sesdir'])
        bidsdir = os.path.join(abs_path_prefix,row['BIDS_dir'])
        for bdir in [subdir,sesdir,bidsdir]:
            if not os.path.isdir(bdir):
                os.mkdir(bdir)
        shutil.copy(i,os.path.join(move_to,row['new_path']))
        count+=1
    print('finished')