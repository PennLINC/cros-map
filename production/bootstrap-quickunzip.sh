#!/bin/bash
#$ -S /bin/bash
#$ -l h_vmem=5G
#$ -l s_vmem=3.5G
# Set up the correct conda environment
source ${CONDA_PREFIX}/bin/activate base


# used to extract all outputs from xcp 
PROJECTROOT=/cbica/projects/rosmap_fmri/production/xcp-multises # ALERT! NEED TO CHANGE THIS PATH TO YOUR XCP BOOTSTRAP DIR 
mkdir -p ${HOME}/DERIVATIVES
cd ${HOME}/DERIVATIVES
RIA=${PROJECTROOT}/output_ria
datalad create -c yoda -D "extract pnc xcp results" XCP
cd XCP
datalad clone -d . --reckless ephemeral "ria+file://${RIA}#~data" inputs/data


## the actual compute job specification
cat > code/get_files.sh << "EOT"
#!/bin/bash
set -e -u -x

ZIP_FILE=$1

# Create a xcp/ directory
unzip -n $ZIP_FILE

mv xcp_abcd/sub-* .

rm -rf xcp_abcd

EOT

datalad save -m "Add data extraction code" code

zip_files=$(find inputs/data/ -name '*.zip')
for input_zip in ${zip_files}
do
    subid=$(basename $input_zip | cut -d '_' -f 1)
    html=${subid}.html
    datalad run \
        -i ${input_zip} \
        -o ${subid} \
        -o ${html} \
        -m "unzipped ${input_zip}" \
        --explicit \
        "bash code/get_files.sh ${input_zip}"
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
