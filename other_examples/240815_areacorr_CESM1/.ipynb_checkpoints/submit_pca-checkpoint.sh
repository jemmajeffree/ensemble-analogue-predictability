#!/bin/bash -l
#PBS -N pca
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=04:00:00
#PBS -q casper
#PBS -o pca.o
#PBS -e pca.e
# One job for each 10 ensemble members seems to work best (ACCESS has 40, index is the start)
#PBS -J 0-90:10

module load conda
conda activate jj_default2

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/pca_projection.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/spinoff_EOF_configs/areacorr_eof_config.py"
MASK_LIST="10P,10-30P,30-10P,10P30A,10P30I,10P30N,10P30S"
VAR="tos,zos"

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME $MASK_LIST $VAR $PBS_ARRAY_INDEX $(($PBS_ARRAY_INDEX+10)) 1> log_$MODEL_NAME/$PBS_ARRAY_INDEX'pca.o' 2> log_$MODEL_NAME/$PBS_ARRAY_INDEX'pca.e'
