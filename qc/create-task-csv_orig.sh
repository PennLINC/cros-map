#!/bin/bash
#$ -S /bin/bash
#$ -l h_vmem=25G
#$ -l tmpfree=200G

PROJECTROOT=/cbica/projects/RBC/RBC_DERIVATIVES/pnc_xcp
cd ${PROJECTROOT}

datalad create -D "csv results dir" csvs

## the actual compute job specification
cat > code/concatenator.py << "EOT"

import pandas as pd
from pathlib import Path
import numpy as np
import subprocess
import os
import sys

csv_dir = sys.argv[1]


column_names_singleband = ['sub', 'ses', 'task', 'acq', 'space', 'res', 'desc', 'meanFD', 'relMeansRMSMotion', 'relMaxRMSMotion', 'meanDVInit', 'meanDVFinal','nVolCensored', 'nVolsRemoved', 'motionDVCorrInit', 'motionDVCorrFinal','coregDice', 'coregJaccard', 'coregCrossCorr', 'coregCoverag','normDice', 'normJaccard', 'normCrossCorr', 'normCoverage']


df_singleband = pd.DataFrame(columns = column_names_singleband)

column_names_frac2back = ['sub', 'ses', 'task', 'space', 'res', 'desc', 'meanFD','relMeansRMSMotion', 'relMaxRMSMotion', 'meanDVInit', 'meanDVFinal','nVolCensored', 'nVolsRemoved', 'motionDVCorrInit', 'motionDVCorrFinal','coregDice', 'coregJaccard', 'coregCrossCorr', 'coregCoverag','normDice', 'normJaccard', 'normCrossCorr', 'normCoverage']

df_frac2back = pd.DataFrame(columns = column_names_frac2back)

column_names_idemo = ['sub', 'ses', 'task', 'space', 'res', 'desc', 'meanFD','relMeansRMSMotion', 'relMaxRMSMotion', 'meanDVInit', 'meanDVFinal','nVolCensored', 'nVolsRemoved', 'motionDVCorrInit', 'motionDVCorrFinal','coregDice', 'coregJaccard', 'coregCrossCorr', 'coregCoverag','normDice', 'normJaccard', 'normCrossCorr', 'normCoverage']

df_idemo = pd.DataFrame(columns = column_names_idemo)

for csv_path in Path(csv_dir).rglob('*_ses-PNC1_task-rest_acq-singleband_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv'):
    df_temp = pd.read_csv(str(csv_path))
    df_singleband = pd.concat([df_singleband, df_temp])

for csv_path in Path(csv_dir).rglob('*_ses-PNC1_task-frac2back_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv'):
    df_temp = pd.read_csv(str(csv_path))
    df_frac2back = pd.concat([df_frac2back, df_temp])

for csv_path in Path(csv_dir).rglob('*_ses-PNC1_task-idemo_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv'):
    df_temp = pd.read_csv(str(csv_path))
    df_idemo = pd.concat([df_idemo, df_temp])


output_dir = sys.argv[2]

df_singleband.to_csv(os.path.join(output_dir,r'task-rest_acq-singleband_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv'), index=False)

df_frac2back.to_csv(os.path.join(output_dir,r'task-frac2back_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv'), index=False)

df_idemo.to_csv(os.path.join(output_dir,r'task-idemo_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv'), index=False)
EOT

datalad save -m "Add concatenator script"
datalad run \
    -i 'xcp_abcd/sub-*/ses-PNC1/func/*_ses-PNC1_task-rest_acq-singleband_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    -i 'xcp_abcd/sub-*/ses-PNC1/func/*_ses-PNC1_task-frac2back_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    -i 'xcp_abcd/sub-*/ses-PNC1/func/*_ses-PNC1_task-idemo_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    -o 'csvs/task-rest_acq-singleband_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    -o 'csvs/task-frac2back_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    -o 'csvs/task-idemo_space-MNI152NLin6Asym_desc-qc_res-2_bold.csv' \
    --expand inputs \
    --explicit \
    -m 'Create QC csvs for three tasks' \
    "python code/concatenator.py ~/RBC_DERIVATIVES/pnc_xcp/xcp_abcd ~/RBC_DERIVATIVES/pnc_xcp/csvs"

datalad save -m "Generated QC csvs"


echo SUCCESS
