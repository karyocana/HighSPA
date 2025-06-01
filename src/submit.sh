#!/bin/bash
#SBATCH --nodes 1
#SBATCH --ntasks-per-node=48
#SBATCH -p desired_partition
#SBATCH --exclusive
#SBATCH --j HighSPA
#SBATCH --time=00:20:00
#SBATCH -e slurm-%j.err
#SBATCH -o slurm-%j.out


module load mafft
module load anaconda3/2024.02_sequana
eval "$(conda shell.bash hook)"
CONDA_ENV="/path/to/conda/env
conda activate ${CONDA_ENV}
CDIR="/path/to/HighSPA"
INPUT_FOLDER="${CDIR}/examples/inputs"
OUTPUT_FOLDER="${CDIR}/output"
EXECUTABLES="${CDIR}/executables.json
ENV_FILE="${CDIR}/path/to/env_file
mkdir -p $OUTPUT_FOLDER

export CONDA_ENV
python parslCodeml.py -i ${INPUT_FOLDER} -o ${OUTPUT_FOLDER} -e ${EXECUTABLES} -env ${ENV_FILE} --onslurm
