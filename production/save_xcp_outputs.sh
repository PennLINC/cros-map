#!/bin/bash
#$ -N save_XCP_outputs
#$ -l h_vmem=64G

# Set up the correct conda environment
source ${CONDA_PREFIX}/bin/activate base
echo I\'m in $PWD using `which python`

datalad save -d ~/DERIVATIVES/XCP -m "copied the extra 63 XCP outputs from the production rerun into this dataset"
