#!/usr/bin/env pythons
import sys, os, parsl
from parsl import load, python_app, bash_app
#from configs.config_HTEx import config
from parsl.data_provider.files import File
from pathlib import Path
 
#load(config)

# Start Parsl on a single computer
parsl.load()


@bash_app
def mafft(multithread_parameter, infile, outputs=[], stderr=None):
    return 'mafft --thread {0} {1} > {2}'.format(multithread_parameter, infile, outputs[0])
#print(mafft().result())

def readseq(output_dir=[], prefix=[], inputs=[], outputs=[], stdout=None, stderr=None):
    import os
    os.mkdir(output_dir)
    return 'java -jar /Users/karyocana/bioinfo/PhyloHPC/programs/readseq.jar -all -f=12 {} -o {}'.format(output_dir, prefix)

#print(readseq().result())

multithread = sys.argv[1]
inputs_mafft = sys.argv[2]
dir_outputs = sys.argv[3]

p = Path(inputs_mafft)
fasta = list(p.glob('*'))

mafft_futures, readseq_futures = [], []


# MAFFT
for i in fasta:
    prefix = Path(Path(i).stem).stem
    output_mafft = '{}/{}.mafft'.format(dir_outputs, prefix)
    stderr_mafft = '{}/stderr/{}.mafft'.format(dir_outputs, prefix)
    infile = str(i)
    mafft_futures.append(mafft(multithread, outputs=[File(output_mafft)], stderr=stderr_mafft))

# READSEQ
for p in mafft_futures:
    prefix = str(Path(p.outputs[0].filename).stem)
    output_readseq = '{}/{}.phylip'.format(dir_outputs, prefix)
    stderr_readseq = '{}/stderr/{}.readseq'.format(dir_outputs, prefix)
    readseq_futures.append(readseq(inputs=p.outputs[0], outputs=[File(output_readseq)], stderr=stderr_readseq))


#def readseq():
#    return 'java -jar /Users/karyocana/bioinfo/PhyloHPC/programs/readseq.jar -all -f=12 tes.mafft -o test.phylip'
#print(readseq().result())

#def readseq():
#    return 'java -jar /Users/karyocana/bioinfo/PhyloHPC/programs/readseq.jar -all -f=12 tes.mafft -o test.phylip'
#print(readseq().result())
#formatPhylip
#python /root/Dropbox/workflow_scievol/perl_script/format_phylip.py %=DIREXP%%=FASTA_FILE%.phylip


#raxml
#codemlM0

#print(mafft().result())




#base_mafft = sys.argv[1] 
#multithread = sys.argv[2]
#inputs_mafft = sys.argv[3]
#dir_outputs = sys.argv[4]

#p = Path(inputs_mafft)
#fasta = list(p.glob('*'))
