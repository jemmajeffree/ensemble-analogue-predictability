#!/bin/bash -l
#PBS -N correlation
#PBS -P x77
#PBS -q normalbw 
#PBS -l mem=63gb 
#PBS -l ncpus=14
#PBS -l jobfs=10gb
#PBS -l walltime=00:30:00
#PBS -l storage=gdata/x77+gdata/xp65+scratch/x77+gdata/su28
#PBS -o corr.o
#PBS -e corr.e

module use /g/data3/xp65/public/modules
module load conda/analysis3

SCRIPT_NAME="/g/data/x77/jj8842/ensemble-analogue-predictability/spinoff_EOF_configs/correlation_area.py"
CONFIG_FILE="/g/data/x77/jj8842/ensemble-analogue-predictability/spinoff_EOF_configs/areacorr_eof_config_asymmetry.py"

mkdir 'log_'$MODEL_NAME

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME 1> log_$MODEL_NAME/corr.o 2> log_$MODEL_NAME/corr.e
