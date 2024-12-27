#!/bin/bash
#SBATCH --nodes 1
#SBATCH --ntasks-per-node=48
#SBATCH -p sequana_cpu_dev
#SBATCH --exclusive
#SBATCH --j ParslCodeML
#SBATCH --time=00:20:00
#SBATCH -e slurm-%j.err
#SBATCH -o slurm-%j.out


module load mafft
module load anaconda3/2024.02_sequana
eval "$(conda shell.bash hook)"
CONDA_ENV="/scratch/cenapadrjsd/rafael.terra2/conda_envs/parslcodeml"
conda activate ${CONDA_ENV}
export CONDA_ENV #This variable should be with the same name and exported because when using HTE, the code will search for it.
CDIR="/scratch/cenapadrjsd/rafael.terra2/ParslCodeml"
INPUT_FOLDER="${CDIR}/examples/inputs"
OUTPUT_FOLDER="${CDIR}/saida_denv"
EXECUTABLES="${CDIR}/executables.json
mkdir -p $OUTPUT_FOLDER

python parslCodeml.py -i ${INPUT_FOLDER} -o ${OUTPUT_FOLDER} -e ${EXECUTABLES} -m
