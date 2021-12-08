import os
import pandas
from glob import glob
redos = sorted(glob('/cbica/projects/rosmap_fmri/example_for_azeez/sub-*'))
redos = [os.path.split(x)[1] for x in redos]
submitter = '/cbica/projects/rosmap_fmri/production_rerun/xcp-multises/analysis/code/qsub_calls.sh'
df = pandas.read_csv(submitter)
inds = []
for i,row in df.iterrows():
    if any([x in row['#!/bin/bash'] for x in redos]):
        inds.append(i)
df = df.loc[inds]
df = df.reset_index()

l_cmd = []
for row in range(len(df)):
    l_cmd.append(df.loc[row, '#!/bin/bash'])
full_cmd = "\n".join(l_cmd)
fileObject = open(boot_dir + "/analysis/code/qsub_calls_rerun.sh","w")
fileObject.write("#!/bin/bash\n")
fileObject.write(full_cmd)

# Close the file
fileObject.close()

