#!/bin/bash -l
#PBS -N correlation
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=00:20:00
#PBS -q casper
#PBS -o corr.o
#PBS -e corr.e

module load conda
conda activate jj_default

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/correlation.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/base_eof_config.py"
MODEL_NAME="ACCESS-ESM1-5"

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME
