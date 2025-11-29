#!/bin/bash -l
#PBS -N correlation
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=04:00:00
#PBS -q casper
#PBS -o corr.o
#PBS -e corr.e

module load conda
conda activate jj_default2

# echo "Hello World"

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/spinoff_EOF_configs/area_correlation_setup.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/spinoff_EOF_configs/area_weight_eof_config.py"

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME 1> log_$MODEL_NAME/${masks[$PBS_ARRAY_INDEX]}corr.o 2> log_$MODEL_NAME/${masks[$PBS_ARRAY_INDEX]}corr.e
