# -*- coding: utf-8 -*-
import requests
import yfinance as yf
import pandas as pd

TOKEN_BRAPI = "qJH13J2kHzxkgBPcMy6STj"

def buscar_dados_brapi(ticker):
    """
    Busca o histórico de dividendos via BRAPI e formata no padrão esperado pelo OASIS35.
    """
    ticker_limpo = str(ticker).replace(".SA", "").strip().upper()
    historico_divs = []

    # 1. TENTA ENDPOINT A (Quote com Dividends)
    url_quote = f"https://brapi.dev/api/v2/stocks/quote?symbols={ticker_limpo}.SA&dividends=true&token={TOKEN_BRAPI}"
    try:
        resp = requests.get(url_quote, timeout=10)
        if resp.status_code == 200:
            dados = resp.json()
            if dados.get("results"):
                historico_divs = dados["results"][0].get("dividendsData", {}).get("cashDividends", [])
    except Exception:
        pass

    # 2. TENTA ENDPOINT B (Prime Dividends para FIIs novos como JMBI11)
    if not historico_divs:
        url_divs = f"https://brapi.dev/api/v2/prime/dividends?ticker={ticker_limpo}&token={TOKEN_BRAPI}"
        try:
            resp_div = requests.get(url_divs, timeout=10)
            if resp_div.status_code == 200:
                dados_div = resp_div.json()
                historico_divs = dados_div.get("results", [])
        except Exception:
            pass

    # Se a BRAPI zerar/falhar, vai para o Yahoo Finance
    if not historico_divs:
        return buscar_dados_yahoo(ticker_limpo)

    # Busca historico de cotações para casar o preço na Data COM
    try:
        ativo_yf = yf.Ticker(f"{ticker_limpo}.SA")
        df_hist = ativo_yf.history(period="max", auto_adjust=False)
        if not df_hist.empty:
            df_hist.index = df_hist.index.tz_localize(None)
    except Exception:
        df_hist = pd.DataFrame()

    registros = []
    for div in historico_divs:
        raw_com = div.get("declarationDate") or div.get("approvedOn") or div.get("paymentDate") or div.get("date")
        raw_pag = div.get("paymentDate")
        
        if not raw_com:
            continue

        dt_com_obj = pd.to_datetime(str(raw_com)[:10], errors='coerce')
        dt_pag_obj = pd.to_datetime(str(raw_pag)[:10], errors='coerce') if raw_pag else None

        if pd.notnull(dt_com_obj):
            val_dy = float(div.get("rate", 0.0) or div.get("value", 0.0))
            if val_dy <= 0:
                continue

            preco_cot = 0.0
            if not df_hist.empty and 'Close' in df_hist.columns:
                val_fech = df_hist['Close'].asof(dt_com_obj)
                if pd.notnull(val_fech) and val_fech > 0:
                    preco_cot = float(val_fech)

            dt_com_str = dt_com_obj.strftime('%d/%m/%Y')
            dt_pag_str = dt_pag_obj.strftime('%d/%m/%Y') if pd.notnull(dt_pag_obj) else '-'

            registros.append({
                'Data COM': dt_com_str,
                'Data Pagamento': dt_pag_str,
                'DY': val_dy,
                'Preço': preco_cot,
                'Cotação PAGT': preco_cot,
                'Yield (%)': (val_dy / preco_cot * 100) if preco_cot > 0 else 0.0,
                'Data_DT': dt_com_obj
            })

    if registros:
        df = pd.DataFrame(registros)
        df['Mês/Ano'] = df['Data_DT'].dt.strftime('%b / %y')
        return df

    return buscar_dados_yahoo(ticker_limpo)


def buscar_dados_yahoo(ticker):
    """
    Fallback usando Yahoo Finance formatado para a estrutura do OASIS35.
    """
    ticker_limpo = str(ticker).replace(".SA", "").strip().upper()
    ticker_yf = f"{ticker_limpo}.SA"
    
    try:
        fii_yf = yf.Ticker(ticker_yf)
        
        # Pega proventos do Yahoo
        df_divs = fii_yf.dividends
        if df_divs.empty:
            return pd.DataFrame()

        hist = fii_yf.history(period="5y", auto_adjust=False)
        if not hist.empty:
            hist.index = hist.index.tz_localize(None)

        dados_yf = []
        for dt, val_dy in df_divs.items():
            val_dy = float(val_dy)
            if val_dy <= 0:
                continue

            dt_clean = dt.tz_localize(None) if hasattr(dt, 'tz_localize') and dt.tz else dt
            
            preco_cot = 0.0
            if not hist.empty and 'Close' in hist.columns:
                val_f = hist['Close'].asof(dt_clean)
                if pd.notnull(val_f) and val_f > 0:
                    preco_cot = float(val_f)

            # Correção de anomalias conhecidas no SNAG11 do Yahoo
            if ticker_limpo == 'SNAG11':
                if val_dy > 0.30:
                    val_dy = val_dy / 10
                elif val_dy < 0.08 and dt_clean.year == 2022:
                    val_dy = 0.12

            # Cotação zerada de segurança
            if preco_cot <= 0:
                preco_cot = 10.0 if ticker_limpo == 'SNAG11' else 100.0

            dados_yf.append({
                'Mês/Ano': dt_clean.strftime('%b / %y'),
                'Data COM': dt_clean.strftime('%d/%m/%Y'),
                'Data Pagamento': '-',
                'DY': val_dy,
                'Preço': preco_cot,
                'Cotação PAGT': preco_cot,
                'Yield (%)': (val_dy / preco_cot * 100) if preco_cot > 0 else 0.0,
                'Data_DT': dt_clean
            })

        if dados_yf:
            return pd.DataFrame(dados_yf)

    except Exception:
        pass

    return pd.DataFrame()
