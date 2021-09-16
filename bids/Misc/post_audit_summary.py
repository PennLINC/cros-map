import os
import mmap
import pandas
from glob import glob

audit_csv = '/cbica/projects/rosmap_fmri/exemplar_test/audit.csv'
log_pth = '/cbica/projects/rosmap_fmri/exemplar_test/fmriprep-multises/analysis/logs/'
acq_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb15_iter1_AcqGrouping.csv'
outfile = '/cbica/projects/rosmap_fmri/exemplar_test/audit_updated.csv'

df = pandas.read_csv(audit_csv,index_col=0)
df.index=range(len(df.index))
acq = pandas.read_csv(acq_pth)
df.loc[df.HasOutput,'AuditStatus'] = 'Pass'
df.loc[df.HasBold==False,'AuditStatus'] = 'NoBOLD'

print('Finding errors types')
all_accounted = False
while not all_accounted:
    errored = df[pandas.isnull(df.AuditStatus)]
    print('an error exemplar:', errored.SubjectID.values[0])
    print('Check this subjects output and find a unique search string for their error')
    answered = False
    while not answered:
        search_string = input('What is the search string? ')
        errtype = input('Should I search in the e or o files (respond e or o): ')
        if errtype not in ['e','o']:
            print('you didnt respond with "e" or "o". Starting over.')
            continue
        errname = input('Give a category to describe the error: ')
        answered = True
    for i,row in errored.iterrows():
        log = sorted(glob(os.path.join(log_pth,'*%s.%s*'%(row.SubjectID,errtype))))[0]
        with open(log, 'rb', 0) as file, \
          mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
            if s.find(search_string.encode()) != -1:
                df.loc[i,'AuditStatus'] = errname
                df.loc[i,'AuditString'] = search_string
    print('found %s subjects with this error'%len(df[df.AuditStatus==errname]),'\n \n')
    if len(df[pandas.isnull(df.AuditStatus)]) == 0:
        all_accounted = True

print('Counting how many subjects errors affect')
for i,row in df.iterrows():
    sub,ses = row['SubjectID'].split('_')
    ses = ses[-1]
    match = acq[(acq.subject==sub) & (acq.session==int(ses))]
    ag = match.AcqGroup.values[0]
    df.loc[i,'AcqGroup'] = ag
    df.loc[i,'AcqGroupN'] = len(acq[acq.AcqGroup==ag])

print('='*10)
print('Here are Acq Groups of failing subjects')
for stat in df.AuditStatus.unique():
    if stat == 'Pass': continue
    print('AcqGroups for %s: %s'%(stat,df[df.AuditStatus==stat].AcqGroup.unique()))

print('='*10)
print('Here is estimate of affected scans per error type')
ns = {}
for ag in df.AcqGroup.unique():
    vcs = df[df.AcqGroup==ag].AuditStatus.value_counts()
    if len(vcs) == 1:
        err = vcs.index[0]
        n = df[df.AcqGroup==ag].AcqGroupN.values[0]
        if err in ns.keys():
            ns.update({err: ns[err]+n})
        else:
            ns.update({err: n})
    else:
        total_n = len(df[df.AcqGroup==ag])
        for err,numer in vcs.items():
            frac = numer/total_n
            n = round(df[df.AcqGroup==ag].AcqGroupN.values[0] * frac)
            if err in ns.keys():
                ns.update({err: ns[err]+n})
            else:
                ns.update({err: n})
for k,v in ns.items():
    print(k,v)

df.to_csv(outfile)
