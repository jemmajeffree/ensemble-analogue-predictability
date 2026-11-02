#!/bin/bash -l

# for MODEL_NAME in 'ACCESS-ESM1-5_nomean' 'CanESM5_nomean' 'GFDL-ESM2M_nomean' 'IPSL-CM6A-LR_nomean' 'MIROC-ES2L_nomean' 'MIROC6_nomean' 'MPI-ESM1-2-LR_nomean' 'MPI-ESM_nomean';

for MODEL_NAME in 'GFDL-ESM2M_nomean' 'IPSL-CM6A-LR_nomean' 'MPI-ESM1-2-LR_nomean' 'MPI-ESM_nomean';
do
# MODEL_NAME=$MODEL_NAME'_nomean'
echo $MODEL_NAME

# mkdir log_$MODEL_NAME

# CORR_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_corr.sh)
# echo "corr: "$CORR_ID

# EOF_ID=$(qsub -r y -W depend=afterok:$CORR_ID -v MODEL_NAME=$MODEL_NAME submit_eof.sh)
# echo "eof: "$EOF_ID

# PCA_ID=$(qsub -r y -W depend=afterok:$EOF_ID -v MODEL_NAME=$MODEL_NAME submit_pca.sh)
# echo "pca: "$PCA_ID

# ANALOG_ID=$(qsub -r y -W depend=afterok:$PCA_ID -v MODEL_NAME=$MODEL_NAME submit_analogue.sh)
ANALOG_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_analogue.sh)
echo "analogue: "$ANALOG_ID
done
