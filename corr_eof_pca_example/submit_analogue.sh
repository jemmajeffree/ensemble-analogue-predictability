#!/bin/bash -l
# PBS -N analogue
# PBS -A UNOA0008
# PBS -l select=1:ncpus=4:mpiprocs=1:mem=40GB:ompthreads=1
# PBS -l place=scatter
# PBS -l walltime=04:00:00
# PBS -q casper
# PBS -o pca.o
# PBS -e pca.e
# One job for each library (ACCESS has 40 members, so 8 libraries of 5 members)
# PBS -J 0-2:1

module load conda
conda activate jj_default

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/base_analogue_forecasting.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/base_eof_config.py"
MODEL_NAME="ACCESS-ESM1-5"
MASK_LIST="30P,30P30A"
VAR="tos,zos"

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME $MASK_LIST $VAR $PBS_ARRAY_INDEX  1> 'analog'$(($PBS_ARRAY_INDEX))'.o' 2> 'analog'$(($PBS_ARRAY_INDEX))'.e'
