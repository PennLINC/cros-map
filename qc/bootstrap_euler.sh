#!/bin/bash
#$ -R y 

source ${CONDA_PREFIX}/bin/activate base
echo I\'m in $PWD using `which python`

python /cbica/projects/rosmap_fmri/general_code/bootstrap_euler.py
