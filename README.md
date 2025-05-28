# HighSPA - High Performance Selection Pressure Analysis Framework
HighSPA is a scientific workflow framework that integrates ParslCodeML and ParslHyPhy for high-throughput analyses of selection pressure.

# ParslCodeml
ParslCodeml is a Python workflow designed to automate phylogenetic analyses using a series of bioinformatics tools. It leverages the Parsl parallel computing library to handle multiple tasks efficiently, making it an ideal choice for large-scale sequence processing pipelines.

## Features
- MAFFT: Aligns sequence data in FASTA format.
- Readseq: Converts aligned sequences into PHYLIP format.
- Custom PHYLIP Formatter: Further processes PHYLIP files for compatibility.
- RAxML: Constructs phylogenetic trees using maximum likelihood methods.
- Codeml (PAML): Performs evolutionary model analysis on phylogenetic data.

## Installation
### Requirements
- [Python](https://www.python.org/) 3.8 or later
- [Parsl](https://parsl-project.org/)
- [MAFFT](https://mafft.cbrc.jp/)
- [Java](https://www.java.com/es/) (for [Readseq](https://bioinformatics.org/~thomas/mol_lin/readseq/)])
- [PAML](http://abacus.gene.ucl.ac.uk/software/paml.html) (codeml)
- [RAxML](https://cme.h-its.org/exelixis/web/software/raxml/)
- Additional Python dependencies (see requirements.txt)
### Setup
1. Clone this repository:
```
git clone https://github.com/yourusername/ParslCodeml.git
cd ParslCodeml
```
2. Create and activate a virtual environment:
```
python3 -m venv parsl_env
source parsl_env/bin/activate
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Configure external tools:
- Ensure MAFFT, RAxML, and codeml are available in your PATH.
- Update paths in the script to point to your readseq.jar and Codeml template directories.

## Usage
### Requirements
```
python3 parslCodeml.py <threads> <input_directory> <output_directory>
```
- threads: Number of threads for parallel processing.
- input_directory: Path to the directory containing input FASTA files.
- output_directory: Path where outputs and logs will be saved.
### Example
```
python3 parslCodeml.py 4 ./inputs ./outputs
```
### Activate Virtual Environment
Before running the script, activate the virtual environment:
```
source parsl_env/bin/activate
```
To deactivate:
source parsl_env/bin/deactivate

## Workflow
1. Input: Provide a directory of FASTA files for sequence analysis.
2. Execution:
- Align sequences with MAFFT.
- Convert formats using Readseq and custom Python scripts.
- Generate phylogenetic trees using RAxML.
- Perform evolutionary model analysis with Codeml for predefined models (M0, M1, M2, M3, M7, M8).
3. Output: Results are saved in the specified output directory, organized by analysis type and model.

## Configuration
- Modify the Parsl configuration in the script to suit your environment:
```
local_config = Config(
    executors=[ThreadPoolExecutor(label="local", max_threads=4)],
    strategy='simple',
    retries=0
)
```
- Update paths for ```readseq.jar```, Codeml templates, and other dependencies as required.

## Troubleshooting
- Ensure all external tools are installed and accessible.
- Verify file permissions for input and output directories.
- Check error logs in the stderr directory under the output path for details on failed tasks.

## License
This project is licensed under the [MIT License](./LICENSE).

## Acknowledgments
- Developed using [Parsl](https://parsl-project.org/) for parallel task execution.
- Utilizes tools from the PAML suite, MAFFT, and RAxML for bioinformatics analyses.






