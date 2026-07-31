import pandas as pd

def preparar_dataframe(df, ativos):
    """
    Garante que qualquer FII (da carteira ou de fora) possa ser processado.
    Se 'df' estiver vazio ou faltarem FIIs que estão na base geral de 'ativos',
    o código une os dados mantendo todos os FIIs disponíveis para consulta.
    """
    if df is None or df.empty:
        # Se não houver dados de carteira, retorna a base total de ativos
        return ativos.copy()

    # Realiza um merge do tipo 'outer' para garantir que FIIs
    # fora da carteira também permaneçam no DataFrame final
    df_resultado = pd.merge(
        df,
        ativos,
        on="FII",
        how="outer"
    )

    return df_resultado

def consultar_fii(ticker, df_completo):
    """
    Função utilitária no CORE para buscar qualquer FII pelo Ticker/Código.
    """
    ticker = str(ticker).strip().upper()
    resultado = df_completo[df_completo["FII"].astype(str).str.upper() == ticker]
    
    if resultado.empty:
        print(f"Aviso: O FII '{ticker}' não foi encontrado na base de dados.")
    
    return resultado
