#!/bin/bash -l
#PBS -N analogue
#PBS -P x77
#PBS -q normalbw 
#PBS -l mem=126gb 
#PBS -l ncpus=28
#PBS -l jobfs=10gb
#PBS -l walltime=04:30:00
#PBS -l storage=gdata/x77+gdata/xp65+scratch/x77+gdata/su28
#PBS -o analogue.o
#PBS -e analogue.e
#One job for each library, jobs for members that don't exist just return early
###PBS -J 0-2:1

module use /g/data3/xp65/public/modules
module load conda/analysis3
cd /g/data/x77/jj8842/ensemble-analogue-predictability/other_examples/260825_biglib_for_asymmetry/

SCRIPT_NAME="/g/data/x77/jj8842/ensemble-analogue-predictability/analogue_forecasting_biglib_asymmetry.py"
CONFIG_FILE="/g/data/x77/jj8842/ensemble-analogue-predictability/spinoff_EOF_configs/areacorr_eof_config_asymmetry.py"

MASK_LIST="30P30A30I"
VAR="tos,zos"
PBS_ARRAY_INDEX=0

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME $MASK_LIST $VAR $PBS_ARRAY_INDEX  1> log_$MODEL_NAME/'analog'$PBS_ARRAY_INDEX'.o' 2> log_$MODEL_NAME/'analog'$PBS_ARRAY_INDEX'.e'
