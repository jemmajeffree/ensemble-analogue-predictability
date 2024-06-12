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
#PBS -J 0-1:1

module load conda
conda activate jj_default

SCRIPT_NAME="/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py"
CONFIG_FILE="/glade/u/home/jjeffree/ensemble-analogue-predictability/base_eof_config.py"
MODEL_NAME="ACCESS-ESM1-5"
declare -a masks=("30P" "30P30A")
VARS='tos,zos'

python $SCRIPT_NAME $CONFIG_FILE $MODEL_NAME ${masks[$PBS_ARRAY_INDEX]} $VARS 1> 'eof'${masks[$PBS_ARRAY_INDEX]}'.o' 2> 'eof'${masks[$PBS_ARRAY_INDEX]}'.e'

