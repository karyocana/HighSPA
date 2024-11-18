#!/usr/bin/env python3
import os
import sys
import parsl
import re

from parsl import bash_app
from parsl.data_provider.files import File
from pathlib import Path
from parsl.executors import ThreadPoolExecutor
from parsl.config import Config

# Configuração do Parsl para rodar localmente
local_config = Config(
    executors=[ThreadPoolExecutor(label="local", max_threads=4)],  # Usando ThreadPoolExecutor
    strategy='simple',  # Estrategia simples, mas você pode personalizar
    retries=0
)

# Carregar a configuração do Parsl
parsl.load(local_config)

@bash_app
def mafft(multithread_parameter, infile, outputs=[], stderr=None):
    print(f"Running MAFFT on {infile} with {multithread_parameter} threads.")
    return f'mafft --thread {multithread_parameter} {infile} > {outputs[0]}'

@bash_app
def readseq(infile, prefix, outputs=[], stderr=None):
    print(f"Running Readseq on {infile} with prefix {prefix}.")
    return f'java -jar /Users/karyocana/parslCodeml/scripts/readseq.jar -all -f=12 {infile} -o {outputs[0]}'

@bash_app
def format_phylip(infile, prefix, outputs=[], stderr=None):
    print(f"Formatting Phylip file {infile} with prefix {prefix}.")
    return f'python /Users/karyocana/parslCodeml/scripts/format_phylip.py {infile} > {outputs[0]}'

@bash_app
def raxml(infile, prefix, outputs=[], stderr=None):
    print(f"Running RAxML on {infile} with prefix {prefix}.")
    output_dir = str(outputs[0].url).rsplit('/', 1)[0]
    return f'raxmlHPC -s {infile} -m GTRCAT -n {prefix}_output.tree -w {output_dir} > {outputs[0]} 2>{stderr}'

@bash_app
def codeml(infile, treefile, prefix, model, outputs=[], stderr=None):
 
    # Pega o diretório de saída do argumento da linha de comando (sys.argv[3])
    dir_outputs = sys.argv[3]
    print(f"Diretório de saída (dir_outputs): {dir_outputs}")  # Depuração para verificar o diretório correto

    # Subdiretório específico para o modelo (ex: M0, M1, ...)
    model_output_dir = os.path.join(dir_outputs, model)  # Garantir que o diretório do modelo seja corretamente formado
    print(f"model_output_dir: {model_output_dir}")  # Depuração do diretório do modelo

    # Garantir que o diretório específico do modelo seja criado
    os.makedirs(model_output_dir, exist_ok=True)

    # Caminho para o arquivo .ctl (será gravado no subdiretório do modelo)
    ctl_template_path = f'/Users/karyocana/parslCodeml/scripts/{model}/codeml.ctl'
    new_ctl_path = os.path.join(model_output_dir, "codeml.ctl")  # Caminho correto para o arquivo .ctl

    # Ler o template e substituir as variáveis no arquivo .ctl
    with open(ctl_template_path, 'r') as ctl_file:
        ctl_content = ctl_file.read()

    # Substituir o caminho do arquivo Phylip
    ctl_content = ctl_content.replace("%=FASTA_FILE%-f.phylip", infile)  # Substituir o arquivo Phylip

    # Ajustar o caminho do 'treefile' para o formato correto, mas no diretório geral
    fixed_treefile = os.path.join(dir_outputs, f"RAxML_result.{prefix}_output.tree")  # Caminho correto para o treefile
    print(f"fixed_treefile: {fixed_treefile}")  # Depuração do caminho do treefile

    # Substituir o campo 'treefile' no arquivo .ctl
    ctl_content = re.sub(
        r"treefile\s*=\s*.*",  # Localizar a linha específica de "treefile"
        f"treefile = {fixed_treefile}",  # Substituir com o caminho fixo para o treefile
        ctl_content
    )

    # Corrigir o campo "outfile" com o formato correto
    outfile_path = os.path.join(model_output_dir, f"{model}_{prefix}.results.txt")  # Caminho correto para o outfile
    print(f"outfile_path: {outfile_path}")  # Depuração do caminho do outfile
    ctl_content = re.sub(
        r"outfile\s*=\s*.*",  # Localizar linha de "outfile"
        f"outfile = {outfile_path}   * main result file name",
        ctl_content
    )
    # Escrever o novo arquivo .ctl no diretório do modelo
    with open(new_ctl_path, 'w') as new_ctl_file:
        new_ctl_file.write(ctl_content)

    # Retornar o comando para execução do codeml
    return f'cd {model_output_dir} && /Users/karyocana/Downloads/paml4.8/bin/codeml {new_ctl_path} 2>{stderr}'

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
multithread = int(sys.argv[1])
inputs_mafft = sys.argv[2]
dir_outputs = sys.argv[3]

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