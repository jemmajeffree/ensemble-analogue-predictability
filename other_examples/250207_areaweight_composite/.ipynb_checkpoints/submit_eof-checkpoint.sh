#!/bin/bash -l
#PBS -N eof
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=04:00:00
#PBS -q casper
#PBS -o eof.o
#PBS -e eof.e
# One job for each mask
#PBS -J 0-12:1

module load conda
conda activate jj_default2

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/spinoff_EOF_configs/area_weight_eof_config.py"
declare -a masks=('10P_12m2varagreement30A' '10P_12m2varagreement30I' '10P_12m2varagreement30-10P' '10P_12m2varagreement10-30P' '10P_12m2varagreement30S' '10P_12m2varagreement30N')
VARS='tos,zos'

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME ${masks[$PBS_ARRAY_INDEX]} $VARS 1> log_$MODEL_NAME/${masks[$PBS_ARRAY_INDEX]}eof.o 2> log_$MODEL_NAME/${masks[$PBS_ARRAY_INDEX]}eof.e

