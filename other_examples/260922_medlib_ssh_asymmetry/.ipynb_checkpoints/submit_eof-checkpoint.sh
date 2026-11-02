#!/bin/bash -l
#PBS -N eof
#PBS -P g40
#PBS -q normalbw 
#PBS -l mem=63gb 
#PBS -l ncpus=14
#PBS -l jobfs=10gb
#PBS -l walltime=04:00:00
#PBS -l storage=gdata/x77+gdata/xp65+scratch/x77+gdata/su28
#PBS -o eof.o
#PBS -e eof.e
### One job for each mask
### PBS -J 0-2:1

module use /g/data3/xp65/public/modules
module load conda/analysis3

cd /g/data/x77/jj8842/ensemble-analogue-predictability/other_examples/260922_medlib_ssh_asymmetry/

PBS_ARRAY_INDEX=0
SCRIPT_NAME="/g/data/x77/jj8842/ensemble-analogue-predictability/eof_calculation.py"
CONFIG_FILE="/g/data/x77/jj8842/ensemble-analogue-predictability/spinoff_EOF_configs/areacorr_eof_config_asymmetry2.py"

declare -a masks=("30P30A30I")
VARS='tos,zos'

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME ${masks[$PBS_ARRAY_INDEX]} $VARS 1> log_$MODEL_NAME/${masks[$PBS_ARRAY_INDEX]}eof.o 2> log_$MODEL_NAME/${masks[$PBS_ARRAY_INDEX]}eof.e

