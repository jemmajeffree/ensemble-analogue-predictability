#!/bin/bash -l
#PBS -N analogue
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=04:00:00
#PBS -q casper
#PBS -o analogue.o
#PBS -e analogue.e
# One job for each library, jobs for members that don't exist just return early
#PBS -J 0-19:1

module load conda
conda activate jj_default2

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting_saveall.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/spinoff_EOF_configs/areacorr_eof_config.py"

MASK_LIST="10P30S"#"10P,10-30P,30-10P,10P30A,10P30I,10P30N,10P30S"
VAR="tos,zos"

LEAD_TIMES="0"
INIT_MONTHS="1"

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME $MASK_LIST $VAR $PBS_ARRAY_INDEX $LEAD_TIMES $INIT_MONTHS 1> log_$MODEL_NAME/'analog'$PBS_ARRAY_INDEX'.o' 2> log_$MODEL_NAME/'analog'$PBS_ARRAY_INDEX'.e'
