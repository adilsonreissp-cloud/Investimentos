import pandas as pd
import numpy as np
import yfinance as yf

def obter_dy_12m_direto(ticker, preco_atual):
    """Garante o cálculo do DY 12M buscando o histórico do Yahoo Finance diretamente."""
    try:
        ticker_sa = f"{ticker.strip().upper()}.SA" if not ticker.endswith(".SA") else ticker
        ativo = yf.Ticker(ticker_sa)
        divs = ativo.dividends
        if not divs.empty and preco_atual > 0:
            hoje = pd.Timestamp.now(tz=divs.index.tz) if divs.index.tz else pd.Timestamp.now()
            inicio_12m = hoje - pd.DateOffset(years=1)
            divs_12m = divs[divs.index >= inicio_12m]
            
            if divs_12m.empty:
                divs_12m = divs.tail(12)
                
            if not divs_12m.empty:
                mediana = float(divs_12m.median())
                divs_limpos = divs_12m.apply(lambda x: mediana if x > (mediana * 3.0) else x)
                media_mensal = float(divs_limpos.sum()) / 12.0
                return (media_mensal / preco_atual) * 100
    except Exception:
        pass
    return None


def obter_pvp_direto(ticker, preco_atual):
    """Busca P/VP via Yahoo ou calcula com VPA conhecido de Fiagros se falhar."""
    vpa_conhecido = {
        'VGIA11': 9.48,
        'SNAG11': 10.05,
        'KNCA11': 100.10,
        'RURA11': 10.12
    }
    
    ticker_clean = ticker.strip().upper().replace(".SA", "")
    
    try:
        ativo = yf.Ticker(f"{ticker_clean}.SA")
        info = ativo.info
        vpa = info.get('bookValue') or info.get('navPrice')
        if vpa and float(vpa) > 0 and preco_atual > 0:
            return preco_atual / float(vpa)
    except Exception:
        pass

    if ticker_clean in vpa_conhecido and preco_atual > 0:
        return preco_atual / vpa_conhecido[ticker_clean]

    return None


def calcular_dy_historico(ticker, df_dados, modulo_cotacoes=None):
    """
    Busca o DY Médio Histórico (12m) diretamente do módulo de cotações
    suportando retornos em dicionário ou DataFrame.
    """
    ticker = str(ticker).strip().upper()
    try:
        if modulo_cotacoes:
            if hasattr(modulo_cotacoes, 'buscar_dados_fii_completo'):
                dados = modulo_cotacoes.buscar_dados_fii_completo(ticker, df_dados)
                if dados and dados.get('dy_medio_12m') not in ['N/D', None]:
                    return float(dados['dy_medio_12m'])
            elif hasattr(modulo_cotacoes, 'buscar_historico_proventos'):
                df_hist = modulo_cotacoes.buscar_historico_proventos(ticker)
                if df_hist is not None and not df_hist.empty and 'yield_datacom' in df_hist.columns:
                    return float(df_hist['yield_datacom'].iloc[0])
    except Exception:
        pass
    return None


def comparar_fiis(fii1_in, fii2_in, df_dados, modulo_cotacoes=None):
    fii1 = fii1_in.strip().upper()
    fii2 = fii2_in.strip().upper()

    # Busca no módulo de cotações completo (se disponível)
    dados_ext1 = modulo_cotacoes.buscar_dados_fii_completo(fii1, df_dados) if (modulo_cotacoes and hasattr(modulo_cotacoes, 'buscar_dados_fii_completo')) else {}
    dados_ext2 = modulo_cotacoes.buscar_dados_fii_completo(fii2, df_dados) if (modulo_cotacoes and hasattr(modulo_cotacoes, 'buscar_dados_fii_completo')) else {}

    # 1. Busca local na carteira
    dados_fii1 = df_dados[df_dados['FII'].astype(str).str.upper() == fii1] if df_dados is not None and not df_dados.empty else pd.DataFrame()
    dados_fii2 = df_dados[df_dados['FII'].astype(str).str.upper() == fii2] if df_dados is not None and not df_dados.empty else pd.DataFrame()

    f1 = dados_fii1.iloc[0] if not dados_fii1.empty else {}
    f2 = dados_fii2.iloc[0] if not dados_fii2.empty else {}

    # Atributos Financeiros
    p1 = float(f1.get('PREÇO ATUAL', f1.get('Preço', f1.get('preco', dados_ext1.get('preco', 0.0) or 0.0))))
    p2 = float(f2.get('PREÇO ATUAL', f2.get('Preço', f2.get('preco', dados_ext2.get('preco', 0.0) or 0.0))))

    dy1_bruto = float(f1.get('DY ESPERADO', f1.get('Rendimento', f1.get('renda', dados_ext1.get('ultimo_rendimento', 0.0) or 0.0))))
    dy2_bruto = float(f2.get('DY ESPERADO', f2.get('Rendimento', f2.get('renda', dados_ext2.get('ultimo_rendimento', 0.0) or 0.0))))

    seg1 = str(f1.get('SEGMENTO', f1.get('segmento', dados_ext1.get('segmento', 'Agro' if 'VGIA' in fii1 or 'SNAG' in fii1 else 'Geral / Tijolo'))))
    seg2 = str(f2.get('SEGMENTO', f2.get('segmento', dados_ext2.get('segmento', 'Agro' if 'VGIA' in fii2 or 'SNAG' in fii2 else 'Geral / Tijolo'))))

    pvp1 = f1.get('P/VP', f1.get('pvp', dados_ext1.get('pvp', 'N/D')))
    pvp2 = f2.get('P/VP', f2.get('pvp', dados_ext2.get('pvp', 'N/D')))

    status1 = str(f1.get('STATUS', 'Recorrente'))
    status2 = str(f2.get('STATUS', 'Recorrente'))

    # Cálculos de Rendimento
    dy1_mensal = dy1_bruto / 3.0 if (fii1 == "BDIV11" and dy1_bruto > 1.0) else dy1_bruto
    dy2_mensal = dy2_bruto / 3.0 if (fii2 == "BDIV11" and dy2_bruto > 1.0) else dy2_bruto

    y1_perc = (dy1_mensal / p1 * 100) if p1 > 0 else 0.0
    y2_perc = (dy2_mensal / p2 * 100) if p2 > 0 else 0.0

    # DY Histórico 12m
    dy1_hist = calcular_dy_historico(fii1, df_dados, modulo_cotacoes)
    dy2_hist = calcular_dy_historico(fii2, df_dados, modulo_cotacoes)

    # 🛡️ TRAVAS DE SEGURANÇA PARA ELIMINAR O "N/D" DE VEZ
    if pvp1 in ['N/D', None, 0.0]:
        pvp1 = obter_pvp_direto(fii1, p1)
    if pvp2 in ['N/D', None, 0.0]:
        pvp2 = obter_pvp_direto(fii2, p2)

    if dy1_hist in ['N/D', None, 0.0]:
        dy1_hist = obter_dy_12m_direto(fii1, p1)
    if dy2_hist in ['N/D', None, 0.0]:
        dy2_hist = obter_dy_12m_direto(fii2, p2)

    # Cotas
    q1 = int(f1.get('QUANTIDADE', f1.get('Quantidade', 0))) if isinstance(f1, pd.Series) and pd.notnull(f1.get('QUANTIDADE', f1.get('Quantidade', None))) else 0
    q2 = int(f2.get('QUANTIDADE', f2.get('Quantidade', 0))) if isinstance(f2, pd.Series) and pd.notnull(f2.get('QUANTIDADE', f2.get('Quantidade', None))) else 0

    # Formatadores
    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    fmt_pct = lambda v: f"{v:.2f}%".replace(".", ",") if (v is not None and isinstance(v, (int, float)) and v > 0) else "N/D"
    
    def fmt_pvp(v):
        if v in ['N/D', None] or not pd.notnull(v):
            return "N/D"
        try:
            val = float(v)
            txt = f"{val:.2f}".replace(".", ",")
            if val > 1.02 and any(s in seg1.lower() + seg2.lower() for s in ['agro', 'crédito', 'papel', 'recebíveis']):
                return f"{txt} ⚠️ (ÁGIO)"
            return txt
        except ValueError:
            return "N/D"

    # IMPRESSÃO DA TABELA
    print("\n" + "=" * 67)
    print(f"                COMPARADOR DE FIIs (OASIS 2035)")
    print("=" * 67)
    print(f"{'  INDICADOR / MÉTRICAS':<25} | {fii1:^17} | {fii2:^17}")
    print("=" * 67)
    
    # 1. Bloco de Classificação e Valor
    print(f"{'Segmento / Tipo':<25} | {seg1:^17} | {seg2:^17}")
    print(f"{'Preço Atual':<25} | {fmt_br(p1):>17} | {fmt_br(p2):>17}")
    print(f"{'P/VP Est.':<25} | {fmt_pvp(pvp1):>17} | {fmt_pvp(pvp2):>17}")
    print("-" * 67)

    # 2. Bloco de Dividendos
    print(f"{'Último Rendimento (R$)':<25} | {fmt_br(dy1_mensal):>17} | {fmt_br(dy2_mensal):>17}")
    print(f"{'DY Atual (Pontual)':<25} | {fmt_pct(y1_perc) + ' a.m.':>17} | {fmt_pct(y2_perc) + ' a.m.':>17}")
    
    dy1_h_str = (fmt_pct(dy1_hist) + ' a.m.') if dy1_hist else 'N/D'
    dy2_h_str = (fmt_pct(dy2_hist) + ' a.m.') if dy2_hist else 'N/D'
    print(f"{'DY Médio Histórico (12m)':<25} | {dy1_h_str:>17} | {dy2_h_str:>17}")
    print(f"{'Status Rendimento':<25} | {status1:^17} | {status2:^17}")
    print("-" * 67)

    # 3. Bloco de Posição na Carteira
    print(f"{'Cotas na Carteira':<25} | {q1:>17} | {q2:>17}")
    print(f"{'Patrimônio Alocado':<25} | {fmt_br(p1 * q1):>17} | {fmt_br(p2 * q2):>17}")
    print("=" * 67 + "\n")
