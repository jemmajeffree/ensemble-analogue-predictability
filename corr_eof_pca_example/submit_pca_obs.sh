#!/bin/bash -l
#PBS -N pca
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=04:00:00
#PBS -q casper
#PBS -o pca.o
#PBS -e pca.e
module load conda
conda activate jj_default

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/pca_projection.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/base_eof_config.py"
MODEL_NAME="ERSSTv5,ACCESS-ESM1-5"
MASK_LIST="30P,30P30A"
VAR="tos,zos"

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME $MASK_LIST $VAR 0 0 1> 'pca_obs.o' 2> 'pca_obs.e'
