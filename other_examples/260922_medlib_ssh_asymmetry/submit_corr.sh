#!/bin/bash -l
#PBS -N correlation
#PBS -P g40
#PBS -q normalbw 
#PBS -l mem=63gb 
#PBS -l ncpus=14
#PBS -l jobfs=10gb
#PBS -l walltime=01:00:00
#PBS -l storage=gdata/x77+gdata/xp65+scratch/x77+gdata/su28
#PBS -o corr.o
#PBS -e corr.e

module use /g/data3/xp65/public/modules
module load conda/analysis3

cd /g/data/x77/jj8842/ensemble-analogue-predictability/other_examples/260922_medlib_ssh_asymmetry/

SCRIPT_NAME="/g/data/x77/jj8842/ensemble-analogue-predictability/spinoff_EOF_configs/correlation_area.py"
CONFIG_FILE="/g/data/x77/jj8842/ensemble-analogue-predictability/spinoff_EOF_configs/areacorr_eof_config_asymmetry2.py"

mkdir 'log_'$MODEL_NAME

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME 1> log_$MODEL_NAME/corr.o 2> log_$MODEL_NAME/corr.e
