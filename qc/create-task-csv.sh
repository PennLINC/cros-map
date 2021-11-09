#!/bin/bash
#$ -S /bin/bash
#$ -l h_vmem=25G
#$ -l tmpfree=200G

source ${CONDA_PREFIX}/bin/activate base

PROJECTROOT=/cbica/projects/rosmap_fmri/DERIVATIVES/XCP
cd ${PROJECTROOT}

datalad create -D "csv results dir" csvs

## the actual compute job specification
cat > /cbica/projects/rosmap_fmri/general_code/concatenator.py << "EOT"

import pandas as pd
from pathlib import Path
import numpy as np
import subprocess
import os
import sys

csv_dir = sys.argv[1]



column_names_all = ['sub', 'ses', 'task', 'acq', 'space', 'res', 'desc', 'meanFD', 'relMeansRMSMotion', 'relMaxRMSMotion', 'meanDVInit', 'meanDVFinal','nVolCensored', 'nVolsRemoved', 'motionDVCorrInit', 'motionDVCorrFinal','coregDice', 'coregJaccard', 'coregCrossCorr', 'coregCoverag','normDice', 'normJaccard', 'normCrossCorr', 'normCoverage']

df_all = pd.DataFrame(columns = column_names_all)

for csv_path in Path(csv_dir).rglob('*_ses-*MNI152NLin6Asym_desc-qc_res-2_bold.csv'):
    df_temp = pd.read_csv(str(csv_path))
    df_all = pd.concat([df_all, df_temp])


output_dir = sys.argv[2]

df_all.to_csv(os.path.join(output_dir,r'task-rest_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv'), index=False)

EOT

datalad save -m "Add concatenator script"
datalad run \
    -i 'sub-*/*/func/*_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    -o 'csvs/task-rest_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    --expand inputs \
    --explicit \
    -m 'Create QC csvs' \
    "python /cbica/projects/rosmap_fmri/general_code/concatenator.py ~/DERIVATIVES/XCP ~/DERIVATIVES/XCP/csvs"
datalad save -m "Generated QC csvs"


echo SUCCESS
