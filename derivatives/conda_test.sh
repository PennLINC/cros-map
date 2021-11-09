#!/bin/bash

echo $SHELL
source ${CONDA_PREFIX}/bin/activate base
echo I\'m in $PWD using `which python`
