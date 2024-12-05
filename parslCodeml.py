#!/usr/bin/env python3
import os, sys, re, argparse, parsl
from parsl.data_provider.files import File
from pathlib import Path
from datetime import datetime
import parsl.log_utils
from config import *
from apps import *
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="ParslCodeML",
                                     description="Python script designed to automate phylogenetic analyses using a series of bioinformatics tools.")
    parser.add_argument("-t", "--threads", help="Maximum number of threads used by the workflow.", required=True,type=int)
    parser.add_argument("-i", "--input", help="Folder containing the fasta files used by the workflow.", required=True, type=str)
    parser.add_argument("-o", "--output", help="Folder where the outputs will be stored.", required=True, type=str)
    parser.add_argument("-e", "--executables", help="Json file containing the executables' info.", required=True, type=str)
    parser.add_argument("-m", "--monitoring", help="Flag to inform parsl to store metadata about the execution.", action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    # Carregar a configuração do Parsl e verifica o caminho dos executáveis
    cfg = gen_config(threads=args.threads,
                     label="default",
                     monitoring=args.monitoring)
    executables = load_and_check_executables(args.executables)
    logger = parsl.set_file_logger(f"ParslCodeML-{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}")
    parsl.load(cfg)

    # Execução do Codeml, agora puxando o diretório de saída de 'outputs'
    codeml_apps = {
        "M0": codeml,
        "M1": codeml,
        "M2": codeml,
        "M3": codeml,
        "M7": codeml,
        "M8": codeml
    }

    # Pegando os argumentos
    multithread = args.threads
    inputs_mafft = args.input
    dir_outputs = args.output

    # Criando diretórios de saída
    Path(f"{dir_outputs}/stderr").mkdir(parents=True, exist_ok=True)

    # Processando entradas
    p = Path(inputs_mafft)
    fasta = list(p.glob('*'))

    print(f"Found {len(fasta)} files in {inputs_mafft}.")

    # Inicializando as listas de futuros para cada etapa
    mafft_futures, readseq_futures, format_phylip_futures, raxml_futures = [], [], [], []
    codeml_futures = {model: [] for model in ["M0", "M1", "M2", "M3", "M7", "M8"]}

    # Execução do MAFFT
    for i in fasta:
        prefix = Path(i.stem).stem
        output_mafft = f'{dir_outputs}/{prefix}.mafft'
        stderr_mafft = f'{dir_outputs}/stderr/{prefix}.mafft'
        infile = str(i)
        print(f"Starting MAFFT for {infile}, output will be saved to {output_mafft}.")
        mafft_futures.append(mafft(multithread_parameter=multithread, infile=infile, outputs=[File(output_mafft)], stderr=stderr_mafft))
    # Esperar a execução do MAFFT
    mafft_results = [j.result() for j in mafft_futures]

    # Execução do READSEQ, aguardando os resultados de MAFFT
    readseq_futures = []
    for p in mafft_futures:
        prefix = Path(p.outputs[0].filename).stem
        output_readseq = f'{dir_outputs}/{prefix}.phylip'
        stderr_readseq = f'{dir_outputs}/stderr/{prefix}.readseq'
        print(f"Starting Readseq for {p.outputs[0]}, output will be saved to {output_readseq}.")
        readseq_futures.append(readseq(infile=p.outputs[0], prefix=prefix, outputs=[File(output_readseq)], stderr=stderr_readseq))
    # Esperar a execução do Readseq
    readseq_results = [j.result() for j in readseq_futures]

    # Execução do FORMAT_PHYLIP, aguardando os resultados de Readseq
    format_phylip_futures = []
    for p in readseq_futures:
        prefix = Path(p.outputs[0].filename).stem
        output_format = f'{dir_outputs}/{prefix}_formatted.phylip'
        print(f"Starting format_phylip for {p.outputs[0]}, output will be saved to {output_format}.")
        format_phylip_futures.append(format_phylip(infile=p.outputs[0], prefix=prefix, outputs=[File(output_format)], stderr=f'{dir_outputs}/stderr/{prefix}.format_phylip'))
    # Esperar a execução do Format Phylip
    format_phylip_results = [j.result() for j in format_phylip_futures]


    # Execução do RAXML, aguardando os resultados de Format Phylip
    raxml_futures = []
    for p in readseq_futures:
        prefix = Path(p.outputs[0].filename).stem
        output_raxml = f'{dir_outputs}/{prefix}_raxml.tree'
        stderr_raxml = f'{dir_outputs}/stderr/{prefix}.raxml'
        print(f"Starting RAxML for {p.outputs[0]}, output will be saved to {output_raxml}.")
        raxml_futures.append(raxml(infile=p.outputs[0], prefix=prefix, outputs=[File(output_raxml)], stderr=stderr_raxml))
    # Esperar a execução do RAXML
    raxml_results = [j.result() for j in raxml_futures]


    # Inicialização das listas de futuros de Codeml por modelo
    codeml_futures = {model: [] for model in ["M0", "M1", "M2", "M3", "M7", "M8"]}


    # Execução do Codeml, aguardando os resultados de RAXML e Format Phylip
    for model, app in codeml_apps.items():
        for p_format, p_raxml in zip(format_phylip_futures, raxml_futures):
            # Pegando o diretório output, baseado no arquivo de p_format
            #mafft_output_dir = str(p_format.outputs[0].filepath).rsplit('/', 1)[0]  # Caminho base do diretório de saída
            dir_outputs = sys.argv[3]

            # Agora pegamos o prefixo corretamente de p_raxml, sem sufixo '_raxml'
            prefix_raxml = Path(p_raxml.outputs[0].filename).stem.split('_')[0]

            # Corrigir o nome do arquivo de saída para o Codeml
            #output_codeml = f"{mafft_output_dir}/{model}/{model}_{prefix_raxml}.results.txt"
            #stderr_codeml = f"{mafft_output_dir}/stderr/{prefix_raxml}_{model}.codeml"

            output_codeml = f"{dir_outputs}/{model}/{model}_{prefix_raxml}.results.txt"
            stderr_codeml = f"{dir_outputs}/stderr/{prefix_raxml}_{model}.codeml"

            infile = p_format.outputs[0].filepath  # Caminho para o arquivo Phylip formatado
            treefile = p_raxml.outputs[0].filepath  # Caminho para o arquivo de árvore gerado pelo RAxML

            # Adicionar a tarefa de Codeml
            codeml_futures[model].append(
                app(infile=infile, treefile=treefile, prefix=prefix_raxml, model=model, outputs=[File(output_codeml)], stderr=stderr_codeml)
            )

    # Esperando as tarefas terminarem
    mafft_results = [j.result() for j in mafft_futures]
    readseq_results = [j.result() for j in readseq_futures]
    format_phylip_results = [j.result() for j in format_phylip_futures]
    raxml_results = [j.result() for j in raxml_futures]
    codeml_results = {model: [j.result() for j in codeml_futures[model]] for model in codeml_futures}

    print("MAFFT Results:", mafft_results)
    print("Readseq Results:", readseq_results)
    print("Format Phylip Results:", format_phylip_results)
    print("RAxML Results:", raxml_results)
    print("Codeml Results:", codeml_results)


    # Aguardar resultados


    #Executar o script
    #python3 parslCodeml.py 1 /Users/karyocana/parslCodeml/inputs /Users/karyocana/parslCodeml/outputs
    #Activate parsl_env
    #source /Users/karyocana/parslCodeml/parsl_env/bin/activate 
    #deactivate