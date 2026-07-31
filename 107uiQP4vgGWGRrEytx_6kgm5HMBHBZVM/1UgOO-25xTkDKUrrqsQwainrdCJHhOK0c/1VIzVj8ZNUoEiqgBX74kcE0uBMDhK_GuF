import os
import pandas as pd
import requests

PASTA_DADOS = "Dados"

def gerar_dataframe_principal():
    """Carrega as tabelas locais, cruza com a BRAPI e retorna o DataFrame unificado"""
    TOKEN = "qJH13J2kHzxkgBPcMy6STj"
    
    try:
        df_carteira = pd.read_csv(os.path.join(PASTA_DADOS, "carteira.csv"), sep=";")
        df_carteira.columns = df_carteira.columns.str.strip().str.upper()
        df_carteira["FII"] = df_carteira["FII"].str.strip().str.upper()
    except FileNotFoundError:
        df_carteira = pd.DataFrame(columns=["FII", "QUANTIDADE", "PREÇO MÉDIO"])

    try:
        df_ativos = pd.read_csv(os.path.join(PASTA_DADOS, "ativos.csv"), sep=";")
        df_ativos.columns = df_ativos.columns.str.strip().str.upper()
        
        if "TICKER" in df_ativos.columns:
            df_ativos = df_ativos.rename(columns={"TICKER": "FII"})
            
        df_ativos["FII"] = df_ativos["FII"].str.strip().str.upper()
        
        for col in ["CATEGORIA", "SEGMENTO", "GESTORA"]:
            if col in df_ativos.columns:
                df_ativos[col] = df_ativos[col].astype(str).str.strip()
    except FileNotFoundError:
        print("❌ Erro crítico: ativos.csv é obrigatório para o cadastro de mercado.")
        return None

    fiis_carteira = df_carteira["FII"].tolist() if not df_carteira.empty else []
    fiis_mercado = df_ativos["FII"].tolist()
    todos_os_fiis = list(set(fiis_carteira + fiis_mercado))
    dicionario_precos = {}
    print("🔄 Coletando cotações individuais na BRAPI...")
    
    for t in todos_os_fiis:
        ticker_limpo = t.replace(".SA", "").upper()
        url = f"https://brapi.dev/api/v2/stocks/quote?symbols={ticker_limpo}.SA&token={TOKEN}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                dados = response.json()
                if dados.get("results"):
                    preco = dados["results"][0].get("data", {}).get("regularMarketPrice", 0.0)
                    dicionario_precos[t] = preco
                else:
                    dicionario_precos[t] = 0.0
            else:
                print(f"⚠️ Alerta: BRAPI retornou status code {response.status_code} para {ticker_limpo}")
                dicionario_precos[t] = 0.0
        except Exception as e:
            print(f"⚠️ Alerta: Falha ao conectar na BRAPI para {ticker_limpo}: {e}")
            dicionario_precos[t] = 0.0

        # Proteção para o SNAG11 se a API falhar
        if ticker_limpo == "SNAG11" and (dicionario_precos.get(t, 0) < 9.0):
            dicionario_precos[t] = 10.10

    # Monta a tabela unificada antes de devolver para o orquestrador
    lista_precos = []
    for fii in todos_os_fiis:
        preco = dicionario_precos.get(fii, 0.0)
        lista_precos.append({'FII': fii, 'PREÇO ATUAL': preco})

    df_precos = pd.DataFrame(lista_precos)
    df_principal = pd.merge(df_ativos, df_precos, on='FII', how='left')
    df_principal = pd.merge(df_principal, df_carteira, on='FII', how='left')
    df_principal['QUANTIDADE'] = df_principal['QUANTIDADE'].fillna(0).astype(int)

    if 'PREÇO MÉDIO' in df_principal.columns:
        df_principal['PREÇO MÉDIO'] = df_principal['PREÇO MÉDIO'].fillna(0.0)
    elif 'PRECO MEDIO' in df_principal.columns:
        df_principal['PREÇO MÉDIO'] = df_principal['PRECO MEDIO'].fillna(0.0)
    else:
        df_principal['PREÇO MÉDIO'] = 0.0

    return df_principal
