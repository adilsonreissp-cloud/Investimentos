import pandas as pd
import requests
import yfinance as yf
import time
import logging

# Silencia avisos do Yahoo Finance
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

TOKEN_BRAPI = "qJH13J2kHzxkgBPcMy6STj"

# --- TRAVAS DE SEGURANÇA E REGRA DE NEGÓCIO ---
TETO_DY_MENSAL_MAX = 1.50  # Filtra amortizações/distorções acima de 1.5% a.m.
EXCLUIR_FIPS = True         # Ignora FIPs (ex: BDIV11) que exigem Investidor Qualificado

def obter_historico_yahoo(ticker, preco_atual, vpa_brapi):
    """
    Calcula P/VP real e os DYs históricos (2024, 2025 e 2026 Mês)
    """
    pvp_real = 0.0
    dy_mensal_rec = 0.0
    dy_2024 = 0.0
    dy_2025 = 0.0

    try:
        ticker_sa = f"{ticker}.SA"
        fii = yf.Ticker(ticker_sa)
        
        # 1. Prioridade para P/VP: Yahoo info -> Cálculo (Preço / VPA)
        info = fii.info
        if 'priceToBook' in info and info['priceToBook'] is not None and info['priceToBook'] > 0:
            pvp_real = float(info['priceToBook'])
        elif vpa_brapi > 0 and preco_atual > 0:
            pvp_real = preco_atual / vpa_brapi
        else:
            pvp_real = 1.00  # Fallback final se não houver VPA registrado

        divs = fii.dividends
        if not divs.empty:
            # 2. DY Mensal Recorrente Atual (2026)
            ultimos_6 = divs.tail(6)
            if preco_atual > 0:
                dy_mensal_rec = (float(ultimos_6.mean()) / preco_atual) * 100

            # 3. Preço Histórico Ajustado por Anos
            hist_anos = fii.history(start="2024-01-01", end="2025-12-31", auto_adjust=True)
            
            divs_2024 = divs[(divs.index >= '2024-01-01') & (divs.index <= '2024-12-31')]
            divs_2025 = divs[(divs.index >= '2025-01-01') & (divs.index <= '2025-12-31')]

            # Cálculo 2024
            if not divs_2024.empty and not hist_anos.empty:
                soma_divs_24 = divs_2024.sum()
                precos_com_24 = hist_anos.reindex(divs_2024.index, method='nearest')['Close']
                preco_medio_24 = precos_com_24.mean()
                if preco_medio_24 > 0:
                    val_24 = (soma_divs_24 / preco_medio_24) * 100
                    dy_2024 = val_24 if val_24 < 50 else 0.0

            # Cálculo 2025
            if not divs_2025.empty and not hist_anos.empty:
                soma_divs_25 = divs_2025.sum()
                precos_com_25 = hist_anos.reindex(divs_2025.index, method='nearest')['Close']
                preco_medio_25 = precos_com_25.mean()
                if preco_medio_25 > 0:
                    val_25 = (soma_divs_25 / preco_medio_25) * 100
                    dy_2025 = val_25 if val_25 < 50 else 0.0

    except Exception:
        if preco_atual > 0 and vpa_brapi > 0:
            pvp_real = preco_atual / vpa_brapi

    return pvp_real, dy_2024, dy_2025, dy_mensal_rec


def rodar_screener_b3(arquivo_csv="fiis_b3.csv"):
    print("\n==========================================================================================")
    print("        OÁSIS 2035 - SCREENER QUANTITATIVO CAÇADOR DE ASSIMETRIAS (FILTRADO)")
    print("==========================================================================================")
    
    try:
        df_csv = pd.read_csv(arquivo_csv)
        col_ticker = df_csv.columns[0]
        lista_bruta = df_csv[col_ticker].dropna().astype(str).str.upper().str.strip().tolist()
        lista_tickers = [t for t in lista_bruta if len(t) == 6 and t.endswith("11")]
        print(f"🔄 Carregados {len(lista_tickers)} FIIs do arquivo '{arquivo_csv}'.")
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo '{arquivo_csv}': {e}")
        return

    print("📡 Varrendo B3 (BRAPI Cotação/VPA + Yahoo Histórico)...\n")
    resultados = []

    total = len(lista_tickers)
    for idx, ticker in enumerate(lista_tickers, 1):
        url = f"https://brapi.dev/api/quote/{ticker}"
        params = {"token": TOKEN_BRAPI, "fundamental": "true"}

        preco = 0.0
        vpa_brapi = 0.0
        type_fundo = ""

        try:
            print(f"\r🔍 Processando [{idx}/{total}]: {ticker:<6}", end="", flush=True)
            res = requests.get(url, params=params, timeout=8)
            if res.status_code == 200:
                dados = res.json().get("results", [])
                if dados:
                    ativo = dados[0]
                    preco = float(ativo.get("regularMarketPrice") or 0.0)
                    vpa_brapi = float(ativo.get("bookValue") or 0.0)
                    type_fundo = str(ativo.get("type", "")).upper()
        except Exception:
            pass

        if preco > 0:
            # Trava 1: Exclui FIP / Investidor Qualificado se identificado na API
            if EXCLUIR_FIPS and ("FIP" in type_fundo or "QUALIFICADO" in type_fundo):
                continue

            pvp_real, dy_24, dy_25, dy_mensal_rec = obter_historico_yahoo(ticker, preco, vpa_brapi)

            # Trava 2: Exclui anomalias / Amortizações não recorrentes (> 1.5% a.m.)
            if dy_mensal_rec > TETO_DY_MENSAL_MAX:
                continue

            resultados.append({
                "Ticker": ticker,
                "Preço": preco,
                "P/VP": pvp_real,
                "DY_2024": dy_24,
                "DY_2025": dy_25,
                "DY_Mensal": dy_mensal_rec
            })
        
        time.sleep(0.1)

    print("\n\n✅ Varredura com travas de segurança concluída!")

    if not resultados:
        print("❌ Nenhum dado atendeu aos critérios de segurança do Screener.")
        return

    df = pd.DataFrame(resultados)
    df['Rank_DY'] = df['DY_Mensal'].rank(ascending=False, method='min')
    df['Rank_PVP'] = df['P/VP'].rank(ascending=True, method='min')
    df['Score_Final'] = df['Rank_DY'] + df['Rank_PVP']
    
    vencedores = df.sort_values(by='Score_Final').reset_index(drop=True)

    print("\n==========================================================================================")
    print("                        TOP OPORTUNIDADES REAIS (EX-AMORTIZAÇÃO / EX-FIP)")
    print("==========================================================================================")
    print(f"{'Pos':<4} | {'Ticker':<8} | {'Preço':<10} | {'P/VP':<6} | {'DY 2024':<9} | {'DY 2025':<9} | {'DY 2026 (Mês)':<12} | {'Status'}")
    print("------------------------------------------------------------------------------------------")

    for i, row in vencedores.head(15).iterrows():
        p_fmt = f"R$ {row['Preço']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        dy_24_fmt = f"{row['DY_2024']:.1f}% a.a." if row['DY_2024'] > 0 else "N/A"
        dy_25_fmt = f"{row['DY_2025']:.1f}% a.a." if row['DY_2025'] > 0 else "N/A"
        dy_m_fmt = f"{row['DY_Mensal']:.2f}% a.m."
        pvp_val = row['P/VP']

        if pvp_val < 0.90:
            status = "🟢 ALTO DESCONTO"
        elif pvp_val <= 1.00:
            status = "🟢 PREÇO JUSTO"
        else:
            status = "🟡 COM PRÊMIO"

        print(f"{i+1:>2}º  | {row['Ticker']:<8} | {p_fmt:>10} | {pvp_val:>6.2f} | {dy_24_fmt:>9} | {dy_25_fmt:>9} | {dy_m_fmt:>12} | {status}")

    print("==========================================================================================\n")

if __name__ == "__main__":
    rodar_screener_b3()
