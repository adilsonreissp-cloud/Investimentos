import pandas as pd
import os

def carregar_dados_principais():
    # Caminhos dos arquivos (ajuste se suas pastas usarem barras diferentes)
    caminho_carteira = os.path.join('Dados', 'carteira.csv')
    caminho_ativos = os.path.join('Dados', 'ativos.csv')
    
    # 1. Leitura e validação do carteira.csv
    try:
        # Usando sep=';' caso seu CSV use ponto e vírgula, ajuste se for vírgula
        df_carteira = pd.read_csv(caminho_carteira, sep=';')
        
        # Padroniza os nomes dos FIIs para maiúsculo e sem espaços para evitar erros de batimento
        df_carteira['FII'] = df_carteira['FII'].str.strip().str.upper()
        
        # Validação para evitar o KeyError que você teve antes
        colunas_carteira = ['FII', 'Quantidade', 'Preço Médio']
        for col in colunas_carteira:
            if col not in df_carteira.columns:
                raise KeyError(f"Coluna obrigatória '{col}' não encontrada no carteira.csv!")
                
    except FileNotFoundError:
        print(f"Erro: O arquivo {caminho_carteira} não foi encontrado.")
        return None
        
    # 2. Leitura e validação do ativos.csv
    try:
        df_ativos = pd.read_csv(caminho_ativos, sep=';')
        df_ativos['FII'] = df_ativos['FII'].str.strip().str.upper()
        
        colunas_ativos = ['FII', 'Categoria', 'Periodicidade', 'DY esperado']
        for col in colunas_ativos:
            if col not in df_ativos.columns:
                raise KeyError(f"Coluna obrigatória '{col}' não encontrada no ativos.csv!")
                
    except FileNotFoundError:
        print(f"Erro: O arquivo {caminho_ativos} não foi encontrado.")
        return None

    # 3. O Pulo do Gato: Cruzar os dados usando a coluna 'FII' como chave
    # O how='left' garante que todos os FIIs que VOCÊ TEM na carteira continuem aparecendo,
    # mesmo se você esquecer de cadastrar algum no ativos.csv
    df_principal = pd.merge(df_carteira, df_ativos, on='FII', how='left')
    
    # Alerta rápido caso tenha esquecido de cadastrar algum ativo no ativos.csv
    if df_principal['Categoria'].isnull().any():
        ativos_sem_cadastro = df_principal[df_principal['Categoria'].isnull()]['FII'].tolist()
        print(f"⚠️ Atenção: Os seguintes ativos da sua carteira não estão cadastrados em ativos.csv: {ativos_sem_cadastro}")

    return df_principal

# Para testar o módulo:
if __name__ == "__main__":
    df_teste = carregar_dados_principains()
    if df_teste is not None:
        print("--- DATAFRAME PRINCIPAL GERADO COM SUCESSO ---")
        print(df_teste)
