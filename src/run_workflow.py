#!/usr/bin/env python3
import os, sys, re, argparse, glob
from pathlib import Path
from datetime import datetime
import parsl
from parsl.data_provider.files import File
from config import *
from apps import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="ParslCodeML",
                                     description="Python script designed to automate phylogenetic analyses using a series of bioinformatics tools.")
    parser.add_argument(
        "-t", "--threads", help="Maximum number of threads used by the workflow.", required=True, type=int)
    parser.add_argument(
        "-i", "--input", help="Folder containing the fasta files used by the workflow.", required=True, type=str)
    parser.add_argument(
        "-o", "--output", help="Folder where the outputs will be stored.", required=True, type=str)
    parser.add_argument("-e", "--executables",
                        help="Json file containing the executables' info.", required=True, type=str)
    parser.add_argument("-env", "--environment",
                        help="Plain text file containing the environment variables and everything else that should be loaded in the worker node.", required=False, type=str, default=None)
    parser.add_argument("-m", "--monitoring", help="Flag to inform parsl to store metadata about the execution.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--onslurm", help="Flag to inform parsl to execute using the HighThroughput executor.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--hyphy", help="By default the workflow will process the sequences using codeml, with this parameter the workflow will use hyphy instead.", action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    use_hyphy = args.hyphy
    # Carregar a configuração do Parsl e verifica o caminho dos executáveis
    cfg = gen_config(threads=args.threads,
                     label="default",
                     monitoring=args.monitoring, slurm=args.onslurm,
                     environment_file = args.environment)
    executables = load_and_check_executables(args.executables)
    parsl.set_file_logger(
        f"ParslCodeML-{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.log")
    parsl.set_stream_logger(stream=sys.stdout)
    logger = logging.getLogger()
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

    hyphy_apps = {
        "ny": hyphy,
        "meme": hyphy,
        "slac": hyphy,
        "fubar": hyphy,
        "fel": hyphy,
        "absrel": hyphy
    }
    # Pegando os argumentos
    max_threads = args.threads
    inputs = args.input

    # Procurando pelos arquivos fasta no diretório de entrada
    fasta_files = glob.glob(os.path.join(inputs, '**'), recursive=True)
    logger.info(f"Found {len(fasta_files)} files in {inputs}.")
    fasta_files = list(filter(lambda x: os.path.isfile(x), fasta_files))
    # Inicializando as listas de futuros para cada etapa
    codeml_futures = {model: []
                      for model in ["M0", "M1", "M2", "M3", "M7", "M8"]}
    
    hyphy_futures = {model: []
                      for model in ["ny", "meme", "slac", "fubar", "fel", "absrel"]}
    # Execução do MAFFT
    for i in fasta_files:
        prefix = Path(i).stem
        input_fullpath = os.path.dirname(i)
        path_to_add_out = os.path.relpath(input_fullpath, args.input)
        dir_outputs = Path(os.path.join(os.path.join(
            args.output, path_to_add_out), prefix))
        Path.mkdir(Path(dir_outputs), exist_ok=True, parents=True)
        output_mafft = os.path.join(dir_outputs, f"{prefix}.mafft")
        logger.info(f"Starting MAFFT for {
                    i}, output will be saved to {output_mafft}.")
        ret_mafft = mafft(executables, multithread_parameter=1, infile=i,
                          outputs=[File(output_mafft)])
        # Execução do READSEQ, cada um dependendo de um mafft
        # output_readseq = os.path.join(dir_outputs, f"{prefix}.phylip")
        # logger.info(f"Starting Readseq for {
        #            prefix}, output will be saved to {output_readseq}.")
        # ret_readseq = readseq(executables, infile=ret_mafft[0].outputs[0], prefix=prefix, outputs=[
        #                      File(output_readseq)])
        # Formatação do arquivo phylip
        output_formatted_phylip = os.path.join(
            dir_outputs, f"{prefix}_formatted.phylip")
        logger.info(f"Starting format_phylip for {
                    output_mafft}, output will be saved to {output_formatted_phylip}.")
        ret_format_phylip = format_phylip(infile=ret_mafft.outputs[0], prefix=prefix, outputs=[
                                          File(output_formatted_phylip)])

        # Execução do RAXML, aguardando os resultados de Format Phylip
        output_raxml = os.path.join(
            dir_outputs, f"RAxML_result.{prefix}_output.tree")
        logger.info(f"Starting RAxML for {
                    ret_format_phylip}, output will be saved to {output_raxml}.")
        ret_raxml = raxml(executables, infile=ret_mafft.outputs[0], prefix=prefix, outputs=[
                          File(output_raxml)])
        # Execução do Codeml, aguardando os resultados de RAXML e Format Phylip
        if use_hyphy == False:
            for model, app in codeml_apps.items():
                output_codeml = os.path.join(dir_outputs, os.path.join(
                    model, f"{model}_{prefix}.results.txt"))
                # Adicionar a tarefa de Codeml
                codeml_futures[model].append(
                    app(executables, infile=ret_format_phylip.outputs[0], treefile=ret_raxml.outputs[0], prefix=prefix,
                        model=model, dir_outputs=dir_outputs, outputs=[File(output_codeml)])
                )
        else:
            # Execução do Hyphy, aguardando os resultados de RAXML e Phylip (saida do mafft)
            for model, app in hyphy_apps.items():
                output_hyphy = os.path.join(dir_outputs, os.path.join(
                    model, f"{model}_{prefix}.results.txt"))
                # Adicionar a tarefa de Hyphy
                hyphy_futures[model].append(
                    app(executables, infile=ret_mafft.outputs[0], treefile=ret_raxml.outputs[0], prefix=prefix,
                        model=model, dir_outputs=dir_outputs, outputs=[File(output_hyphy)])
                )


    parsl.wait_for_current_tasks()
    logger.info("All tasks were performed! Finishing execution!")
    parsl.dfk().cleanup()

    # Aguardar resultados

    # Executar o script
    # python3 parslCodeml.py 1 /Users/karyocana/parslCodeml/inputs /Users/karyocana/parslCodeml/outputs
    # Activate parsl_env
    # source /Users/karyocana/parslCodeml/parsl_env/bin/activate
    # deactivate
