import sys
import os

def post_process_phylip(PhylipFile, OutputFile = None):
    # Abrir o arquivo phylip e ler seu conteúdo
    try:
        with open(PhylipFile, "r") as f:
            phylip = f.read()
    except IOError as e:
        raise Exception(f"I/O error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")

    # Preparar o caminho para o arquivo de saída
    dirname = os.path.dirname(PhylipFile)
    basename = os.path.splitext(PhylipFile)[0]
    extension = os.path.splitext(PhylipFile)[1]

    # Alterar o sufixo para "_formatted"
    if OutputFile is None:
        OutputFile = f"{basename}_formatted{extension}"

    # Processar o conteúdo do arquivo
    try:
        with open(OutputFile, "w") as o:
            # Escrever a primeira linha modificada com números
            lines = phylip.split("\n")
            firstLine = lines[0]
            num_sequences, num_characters = firstLine.split()[:2]  # Pega apenas os dois primeiros números
            
            # Escrever a nova primeira linha
            o.write(f"{num_sequences} {num_characters} I\n")
            
            # Escrever o restante do conteúdo (preservando as linhas seguintes)
            remaining_phylip = "\n".join(lines[1:])  # Remove a primeira linha
            o.write(remaining_phylip)
        
    except IOError as e:
        raise Exception(f"I/O error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso incorreto. Exemplo: python format_phylip.py arquivo.phylip")
        sys.exit(1)
    
    post_process_phylip(sys.argv[1])
