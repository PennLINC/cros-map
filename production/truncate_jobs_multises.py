import subprocess
import sys
import os
from pathlib import Path
import glob
import pandas as pd

boot_dir = sys.argv[1]

#qstat = subprocess.check_output(['qstat'],shell=True).decode().split('/bin/python')[0]
#lines = qstat.split('\n')

out = subprocess.check_output(['git', 'branch', '-a'], cwd=boot_dir + '/output_ria/alias/data')
branches = out.decode().split()

print(len(branches))

success_subs = []
for branch in branches:
    if branch.startswith('job-'):
        jnk = branch.split('-')
        success_sub = 'sub-%s-ses-%s'%(jnk[3],jnk[5])
        success_subs.append(success_sub)


# NOW truncate qsub_calls.sh!
df = pd.read_csv(boot_dir + '/analysis/code/qsub_calls.sh')
for row in range(len(df)):
    jnk = df.loc[row, '#!/bin/bash'].split(' ')
    sub = '%s-%s'%(jnk[-2],jnk[-1])
    if sub in success_subs:
        # remove that row 
        df.drop([row], inplace = True)

print(len(df))

df = df.reset_index()

# write out qsub_calls_rerun.sh
l_cmd = []
for row in range(len(df)):
    l_cmd.append(df.loc[row, '#!/bin/bash'])
full_cmd = "\n".join(l_cmd)
fileObject = open(boot_dir + "/analysis/code/qsub_calls_rerun.sh","w")
fileObject.write("#!/bin/bash\n")
fileObject.write(full_cmd)

# Close the file
fileObject.close()
