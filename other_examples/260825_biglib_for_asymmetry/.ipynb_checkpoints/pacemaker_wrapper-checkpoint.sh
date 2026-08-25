#!/bin/bash -l
BREAK
for MODEL_NAME in "EC-Earth3_tos_nomean" "GFDL-CM2-1" "CESM1_pi";
do
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
