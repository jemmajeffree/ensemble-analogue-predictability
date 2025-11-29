#!/bin/bash -l
#PBS -N analogue
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=04:00:00
#PBS -q casper
#PBS -o pca.o
#PBS -e pca.e
#One job for each library, jobs for members that don't exist just return early
#PBS -J 0-19:1

module load conda
conda activate jj_default2

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting_saveall.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/spinoff_EOF_configs/area_weight_eof_config.py"

MASK_LIST='10P_12m2varagreement30A,10P_12m2varagreement30I,10P_12m2varagreement30-10P,10P_12m2varagreement10-30P,10P_12m2varagreement30S,10P_12m2varagreement30N'
VAR="tos,zos"

LEAD_TIMES="0"
INIT_MONTHS="1"

python $SCRIPT_NAME $CONFIG_FILE 'composite_5,'$MODEL_NAME $MASK_LIST $VAR $PBS_ARRAY_INDEX $LEAD_TIMES $INIT_MONTHS 1> log_$MODEL_NAME/'analog'$PBS_ARRAY_INDEX'.o' 2> log_$MODEL_NAME/'analog'$PBS_ARRAY_INDEX'.e'
