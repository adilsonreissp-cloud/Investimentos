# metricas_extremas.py
from datetime import datetime, timedelta

def calcular_laboratorio_oasis(fii_dados, taxa_tesouro_2035=6.20, inflacao_estimada=4.0):
    """
    Calcula as métricas avançadas do Manifesto Oásis 2035.
    """
    ticker = fii_dados.get("ticker", "FII")
    preco_atual = float(fii_dados.get("preco_atual", 0.0))
    provento_12m = float(fii_dados.get("provento_12m", 0.0))
    ultimo_provento = float(fii_dados.get("ultimo_provento", 0.0))
    cotas = max(1, int(fii_dados.get("cotas", 1)))
    
    preco_medio_original = float(fii_dados.get("preco_medio_original", preco_atual))
    total_div_recebidos = float(fii_dados.get("total_dividendos_recebidos", 0.0))
    
    # 1. PM Amortizado e YoC
    provento_por_cota_recebido = total_div_recebidos / cotas
    preco_medio_amortizado = max(0.01, preco_medio_original - provento_por_cota_recebido)
    yoc_mensal = (ultimo_provento / preco_medio_amortizado) * 100 if preco_medio_amortizado > 0 else 0.0

    # 2. Spread vs IPCA+ 2035
    dy_12m_nominal = (provento_12m / preco_atual * 100) if preco_atual > 0 else 0.0
    yield_real_fii = dy_12m_nominal - inflacao_estimada
    spread_tesouro = yield_real_fii - taxa_tesouro_2035

    # 3. Cronômetro Data COM (Com suporte a FIIs Trimestrais)
    hoje = datetime.now()
    
    # Regra Trimestral Exclusiva (BDIV11: Jan, Abr, Jul, Out)
    if ticker.upper() == "BDIV11":
        meses_trimestrais = [1, 4, 7, 10]
        data_com_proxima = None
        
        for ano in [hoje.year, hoje.year + 1]:
            for mes in meses_trimestrais:
                try:
                    dt_teste = datetime(ano, mes, 23)
                    if dt_teste.date() > hoje.date():
                        data_com_proxima = dt_teste
                        break
                except ValueError:
                    pass
            if data_com_proxima:
                break
    else:
        # Lógica padrão para FIIs mensais
        dia_padrao = int(fii_dados.get("dia_padrao_data_com", 16))
        try:
            data_com_mes = hoje.replace(day=dia_padrao)
        except ValueError:
            data_com_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        if hoje.day > dia_padrao:
            if hoje.month == 12:
                data_com_proxima = hoje.replace(year=hoje.year + 1, month=1, day=dia_padrao)
            else:
                data_com_proxima = hoje.replace(month=hoje.month + 1, day=dia_padrao)
        else:
            data_com_proxima = data_com_mes

    dias_restantes = (data_com_proxima.date() - hoje.date()).days
    return {
        "ticker": ticker,
        "pm_amortizado": preco_medio_amortizado,
        "yoc_mensal": yoc_mensal,
        "spread": spread_tesouro,
        "dias_data_com": dias_restantes
    }


def exibir_painel_oasis_2035(lista_fiis):
    """
    Exibe a tabela comparativa de Métricas Extremas no terminal FII CONTROL.
    """
    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print("\n" + "=" * 75)
    print("                LABORATÓRIO OÁSIS 2035 - MÉTRICAS EXTREMAS")
    print("=" * 75)
    
    headers = [f"{item['ticker']:^14}" for item in lista_fiis]
    print(f"{'MÉTRICA AVANÇADA':<25} | " + " | ".join(headers))
    print("-" * 75)

    pms = [f"{fmt_br(item['pm_amortizado']):>14}" for item in lista_fiis]
    print(f"{'P.Médio Amortizado':<25} | " + " | ".join(pms))

    yocs = [f"{item['yoc_mensal']:>10.2f}% a.m." for item in lista_fiis]
    print(f"{'YoC Mensal (S/ PM Amort.)':<25} | " + " | ".join(yocs))

    spreads = [f"{item['spread']:>+9.1f}% a.a." for item in lista_fiis]
    print(f"{'Spread vs IPCA+ 2035':<25} | " + " | ".join(spreads))

    gatilhos = []
    for item in lista_fiis:
        dias = item['dias_data_com']
        if dias == 0:
            gatilhos.append(f"{'É HOJE! 🔥':^14}")
        elif dias == 1:
            gatilhos.append(f"{'Amanhã! ⚡':^14}")
        else:
            gatilhos.append(f"{f'Faltam {dias}d':^14}")
            
    print(f"{'Gatilho Data COM':<25} | " + " | ".join(gatilhos))
    
    isencao = [f"{'100% 🟢':^14}" for _ in lista_fiis]
    print(f"{'Eficiência Fiscal':<25} | " + " | ".join(isencao))
    print("=" * 75 + "\n")
