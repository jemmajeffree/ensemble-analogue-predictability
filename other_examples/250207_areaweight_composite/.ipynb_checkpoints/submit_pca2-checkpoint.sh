#!/bin/bash -l
#PBS -N pca
#PBS -A UNOA0008
#PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=04:00:00
#PBS -q casper
#PBS -o pca2.o
#PBS -e pca2.e

module load conda
conda activate jj_default2

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/pca_projection.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/spinoff_EOF_configs/area_weight_eof_config.py"
MASK_LIST='10P_12m2varagreement30A,10P_12m2varagreement30I,10P_12m2varagreement30-10P,10P_12m2varagreement10-30P,10P_12m2varagreement30S,10P_12m2varagreement30N' # 10P,30P,60P,10-30P,30-10P,30P30A,30P30I"
VAR="tos,zos"

python $SCRIPT_NAME $CONFIG_FILE 'composite_5,'$MODEL_NAME $MASK_LIST $VAR 0 0 1> log_$MODEL_NAME/$PBS_ARRAY_INDEX'pca2.o' 2> log_$MODEL_NAME/$PBS_ARRAY_INDEX'pca2.e'
