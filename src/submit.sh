#!/bin/bash
#SBATCH --nodes 1
#SBATCH --ntasks-per-node=48
#SBATCH -p sequana_cpu_dev
#SBATCH --exclusive
#SBATCH --j HighSPA
#SBATCH --time=00:20:00
#SBATCH -e slurm-%j.err
#SBATCH -o slurm-%j.out


module load mafft
module load raxml
module load anaconda3/2024.02_sequana
eval "$(conda shell.bash hook)"
CONDA_ENV="/scratch/cenapadrjsd/rafael.terra2/conda_envs/parsl_test/"
conda activate ${CONDA_ENV}
CDIR="/scratch/cenapadrjsd/rafael.terra2/HighSPA"
INPUT_FOLDER="${CDIR}/bench"
OUTPUT_FOLDER="${CDIR}/output"
EXECUTABLES="${CDIR}/src/executables.json"
ENV_FILE="${CDIR}/src/env"
rm -rf $OUTPUT_FOLDER
mkdir -p $OUTPUT_FOLDER
export CONDA_ENV
python HighSPA.py -i ${INPUT_FOLDER} -o ${OUTPUT_FOLDER} -e ${EXECUTABLES} -env ${ENV_FILE} --onslurm --hyphy -m
