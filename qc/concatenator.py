
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

