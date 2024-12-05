import os, parsl, logging
from parsl.data_provider.files import File
from parsl import bash_app, python_app

logger = logging.getLogger()

@bash_app
def mafft(executables, multithread_parameter, infile, outputs=[], stdout = parsl.AUTO_LOGNAME, stderr=parsl.AUTO_LOGNAME):
    logger.info(f"Running MAFFT on {infile} with {multithread_parameter} threads.")
    return f'{executables["mafft"]} --thread {multithread_parameter} {infile} > {outputs[0]}'

@bash_app
def readseq(executables, infile, prefix, outputs=[], stdout = parsl.AUTO_LOGNAME, stderr=parsl.AUTO_LOGNAME):
    logger.info(f"Running Readseq on {infile} with prefix {prefix}.")
    return f'java -jar {executables["readseq"]} -all -f=12 {infile} -o {outputs[0]}'


@python_app
def format_phylip(infile, prefix, outputs=[], stdout = parsl.AUTO_LOGNAME, stderr=parsl.AUTO_LOGNAME):
    from format_phylip import post_process_phylip
    logger.info(f"Formatting Phylip file {infile} with prefix {prefix}.")
    post_process_phylip(infile, outputs[0])
    return

@bash_app
def raxml(executables, infile, prefix, outputs=[], stdout = parsl.AUTO_LOGNAME, stderr=parsl.AUTO_LOGNAME):
    logger.info(f"Running RAxML on {infile} with prefix {prefix}.")
    output_dir = str(outputs[0].url).rsplit('/', 1)[0]
    return f'{executables["raxml"]} -s {infile} -m GTRCAT -n {prefix}_output.tree -w {output_dir} > {outputs[0]} 2>{stderr}'

@bash_app
def codeml(executables, infile, treefile, prefix, model, outputs=[], stdout = parsl.AUTO_LOGNAME, stderr=parsl.AUTO_LOGNAME):
 
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
    return f"cd {model_output_dir} && {executables['codeml']} {new_ctl_path} 2>{stderr}"

