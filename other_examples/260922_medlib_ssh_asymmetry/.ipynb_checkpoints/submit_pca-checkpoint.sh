#!/bin/bash -l
#PBS -N pca
#PBS -P g40
#PBS -q normalbw 
#PBS -l mem=63gb 
#PBS -l ncpus=14
#PBS -l jobfs=10gb
#PBS -l walltime=04:00:00
#PBS -l storage=gdata/x77+gdata/xp65+scratch/x77+gdata/su28
#PBS -o pca.o
#PBS -e pca.e
# One job for each 10 ensemble members seems to work best (ACCESS has 40, index is the start)
#PBS -J 0-90:10

module use /g/data3/xp65/public/modules
module load conda/analysis3

cd /g/data/x77/jj8842/ensemble-analogue-predictability/other_examples/260922_medlib_ssh_asymmetry/

SCRIPT_NAME="/g/data/x77/jj8842/ensemble-analogue-predictability/pca_projection.py"
CONFIG_FILE="/g/data/x77/jj8842/ensemble-analogue-predictability/spinoff_EOF_configs/areacorr_eof_config_asymmetry2.py"

MASK_LIST="30P30A30I"
VAR="tos,zos"

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME $MASK_LIST $VAR $PBS_ARRAY_INDEX $(($PBS_ARRAY_INDEX+10)) 1> log_$MODEL_NAME/$PBS_ARRAY_INDEX'pca.o' 2> log_$MODEL_NAME/$PBS_ARRAY_INDEX'pca.e'
