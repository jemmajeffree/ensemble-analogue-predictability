#!/bin/bash -l
#PBS -N plot
#PBS -A UNOA0008
#PBS -l select=1:ncpus=8:mpiprocs=1:mem=64GB:ompthreads=1
#PBS -l place=scatter
#PBS -l walltime=01:00:00
#PBS -q casper
#PBS -o plot.o
#PBS -e plot.e

module load conda
conda activate jj_default


python quickplot.py
