import mmap
import pandas
from glob import glob

errs = sorted(glob('/cbica/projects/rosmap_fmri/exemplar_test/fmriprep/analysis/logs/*'))
strs = {b'Exception: No T1w images found for participant': 'NO_T1', 
       b"PhaseEncodingDirection is not defined within the metadata retrieved for the intended EPI (DWI, BOLD, or SBRef) run": 'PhaseEncodingDir_NotSet', 
       b"RuntimeError: No BOLD images found for participant": 'NO_BOLD'}


allsubs = []
reasons = pandas.DataFrame(columns=['Reason'])
ostr = b"traits.trait_errors.TraitError: Each element of the 'in_file' trait of a DynamicTraitedSpec instance must be a pathlike object or string representing an existing file, but a value"
for err in errs:
    sub = err.split('/')[-1].split('.')[0].split('fp')[-1]
    if sub in allsubs:
        continue
    else:
        allsubs.append(sub)
        found = False
    ext = err.split('.')[-1]
    with open(err, 'rb', 0) as file, \
     mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
        for identifier,error in strs.items():
            if s.find(identifier) != -1:
                reasons.loc[sub,'Reason'] = error
                found = True
    if found: continue
    err2 = err.replace(ext,ext.replace('e','o'))
    with open(err2, 'rb', 0) as file, \
          mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
        if s.find(ostr) != -1:
            reasons.loc[sub,'Reason'] = 'phase2_NotPresent'
            found = True
    if not found:
        reasons.loc[sub,'Reason'] = 'Unknown'