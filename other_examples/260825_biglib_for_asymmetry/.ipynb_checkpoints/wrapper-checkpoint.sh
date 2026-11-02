#!/bin/bash -l

for MODEL_NAME in "CanESM5";
do
MODEL_NAME=$MODEL_NAME'_nomean'
echo $MODEL_NAME

# mkdir log_$MODEL_NAME
# -W thingy doesn't work on gadi so I'm just running subsequent jobs manually

# CORR_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_corr.sh)
# echo "corr: "$CORR_ID

EOF_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_eof.sh)
echo "eof: "$EOF_ID

# PCA_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_pca.sh)
# echo "pca: "$PCA_ID

#ANALOG_ID=$(qsub -r y -v MODEL_NAME=$MODEL_NAME submit_analogue.sh)
#echo "analogue: "$ANALOG_ID
done
