#!/bin/bash

source ${CONDA_PREFIX}/bin/activate base
echo I\'m in $PWD using `which python`
# used to extract all outputs from xcp 
PROJECTROOT=/cbica/projects/rosmap_fmri/production/xcp-multises # ALERT! NEED TO CHANGE THIS PATH TO YOUR XCP BOOTSTRAP DIR 

cd /cbica/projects/rosmap_fmri/DERIVATIVES/XCP
zip_files=$(find inputs/data/ -name '*.zip')
for input_zip in ${zip_files}
do
    subid=$(basename $input_zip | cut -d '_' -f 1)
    sesid=$(basename $input_zip | cut -d '_' -f 2)
    html=${subid}_${sesid}.html
    if [[ -f /cbica/projects/rosmap_fmri/DERIVATIVES/XCP/${html} ]]
    then
        echo ${html} UNZIPPED
    else
        echo ${html} NOT UNZIPPED 
        datalad run \
            -i ${input_zip} \
            -o ${subid} \
            -o ${html} \
            -m "unzipped ${input_zip}" \
            --explicit \
            "bash code/get_files.sh ${input_zip}"

    fi
done

echo 'DATALAD RUN FINISHED'

# remove reckless ephemeral clone of zips
rm -rf inputs

# make inputs/data exist again so working directory is clean 
mkdir -p inputs/data

# FOR CONSUMERS OF DATA (if you want to see the inputs/data):
# note that datalad get -n JUST gets the git history of the files 
# datalad clone ~/RBC_DERIVATIVES/PNC/XCP test_xcp_outputs
# datalad get -n inputs/data # to see xcp zips
# datalad get -n inputs/data/inputs/data # to see fmriprep and freesurfer zips
# datalad get -n inputs/data/inputs/data/inputs/data # to see BIDS!

echo 'REMOVED INPUTS'
echo 'SUCCESS'
