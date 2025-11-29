#!/bin/bash -l

for MODEL_NAME in "ACCESS-ESM1-5" "CESM2-LE" "CanESM5" "IPSL-CM6A-L" "GFDL-ES2M" "MIROC6" "MIROC-ES2L" "MPI-GE" "MPI-CMIP6"; #
do
MODEL_NAME=$MODEL_NAME'_nomean'
echo $MODEL_NAME

mkdir log_$MODEL_NAME

ANALOG_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_analogue.sh)
echo "analogue: "$ANALOG_ID
done
