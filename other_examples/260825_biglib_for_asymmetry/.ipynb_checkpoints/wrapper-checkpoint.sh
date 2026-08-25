#!/bin/bash -l

for MODEL_NAME in "ACCESS-ESM1-5" "CESM2-LE" "MPI-GE" "CanESM5" "IPSL-CM6A-L" "GFDL-ES2M" "MIROC6" "MIROC-ES2L" "MPI-CMIP6";
do
MODEL_NAME=$MODEL_NAME'_nomean'
echo $MODEL_NAME

mkdir log_$MODEL_NAME

# CORR_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_corr.sh)
# echo "corr: "$CORR_ID

#EOF_ID=$(qsub -W depend=afterok:$CORR_ID -r y -v MODEL_NAME=$MODEL_NAME submit_eof.sh)
EOF_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_eof.sh)
echo "eof: "$EOF_ID

PCA_ID=$(qsub -W depend=afterok:$EOF_ID -r y -v MODEL_NAME=$MODEL_NAME submit_pca.sh)
echo "pca: "$PCA_ID

ANALOG_ID=$(qsub -W depend=afterok:$PCA_ID -r y -v MODEL_NAME=$MODEL_NAME submit_analogue.sh)
echo "analogue: "$ANALOG_ID
done