import os
import sys

# Detecta automaticamente se está no Android (Termux) ou no Desktop Linux
CAMINHO_DESKTOP = "/run/user/1000/gvfs/google-drive:host=gmail.com,user=adilsonreissp/0ANi7kEn2mUOzUk9PVA/107uiQP4vgGWGRrEytx_6kgm5HMBHBZVM/Dados"
CAMINHO_CELULAR = "/storage/emulated/0/Investimentos/Dados" # ou a pasta do seu Drive/armazenamento no Android

if os.path.exists("/sdcard") or "com.termux" in os.environ.get("PREFIX", ""):
    PASTA_DADOS = CAMINHO_CELULAR
else:
    PASTA_DADOS = CAMINHO_DESKTOP
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv
import pandas as pd
import yfinance as yf
import requests
import logging
import Modulos.cotacoes as cotacoes

# Silencia logs de erro indesejados do yfinance e urllib no terminal
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

from Modulos.log import registrar
from Modulos.radar import calcular_nota
from Modulos.core import preparar_dataframe
from Modulos.motor_oasis import gerar_dataframe_principal
from Modulos.simulacao_oasis import rodar_calculo_cenarios
from Modulos.relatorio_oasis import exportar_relatorio_executivo
from Modulos.historico_oasis import processar_historico_carteira
from Modulos.api_oasis import buscar_dados_brapi as api_brapi, buscar_dados_yahoo as api_yahoo
from Modulos.comparador import comparar_fiis
from Modulos.gerenciador_fiis import menu_gerenciar_fiis
from Modulos.acoes import menu_radar_acoes
from metricas_extremas import calcular_laboratorio_oasis, exibir_painel_oasis_2035

PASTA_DADOS = "/run/user/1000/gvfs/google-drive:host=gmail.com,user=adilsonreissp/0ANi7kEn2mUOzUk9PVA/107uiQP4vgGWGRrEytx_6kgm5HMBHBZVM/Dados"

def mostrar_painel_oasis(df):
    print("\n" + "=" * 90)
    print("                        FII CONTROL - OASIS 2035")
    print("=" * 90)

    if df is None or df.empty:
        print("⚠ Nenhuma informação disponível na carteira.")
        return

    # Tratamento defensivo de colunas numéricas
    df_carteira = df.copy()
    for col in ['QUANTIDADE', 'PREÇO ATUAL', 'DY ESPERADO']:
        if col in df_carteira.columns:
            df_carteira[col] = pd.to_numeric(df_carteira[col], errors='coerce').fillna(0)

    # Filtra apenas o que você possui em custódia
    df_minha_carteira = df_carteira[df_carteira['QUANTIDADE'] > 0].copy()

    if df_minha_carteira.empty:
        print("⚠ Nenhuma cota encontrada com quantidade maior que zero.")
        return

    # Cabeçalho unificado
    print(f"{'FII':<8} {'Qtde':>6}   {'Vlr Unit.':>12}   {'Total Investido':>17}   {'Yield/Mês':>12}   {'Renda Est/Mês':>13}")
    print("-" * 90)

    total_carteira = 0.0
    total_dividendos = 0.0

    for _, linha in df_minha_carteira.iterrows():
        fii_nome = str(linha['FII']).strip().upper().replace(".SA", "")
        qtde = int(linha['QUANTIDADE'])
        preco_unitario = float(linha['PREÇO ATUAL'])
        total_ativo = qtde * preco_unitario
        total_carteira += total_ativo

        dy_esperado_bruto = float(linha.get('DY ESPERADO', 0.0))
        dy_esperado_mensal = dy_esperado_bruto

        dividendo_total_ativo = qtde * dy_esperado_mensal
        total_dividendos += dividendo_total_ativo

        # Yield Percentual Mensal do Ativo
        yield_perc = (dy_esperado_mensal / preco_unitario * 100) if preco_unitario > 0 else 0.0

        # Formatações PT-BR
        vlr_un_fmt = f"R$ {preco_unitario:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        tot_inv_fmt = f"R$ {total_ativo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        dy_esp_fmt = f"R$ {dividendo_total_ativo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        yield_perc_fmt = f"{yield_perc:.2f}%".replace(".", ",")

        print(f"{fii_nome:<8} {qtde:>6}   {vlr_un_fmt:>12}   {tot_inv_fmt:>17}   {yield_perc_fmt:>12}   {dy_esp_fmt:>13}")

    print("-" * 90)

    # Totais da Carteira
    yield_medio_carteira = (total_dividendos / total_carteira * 100) if total_carteira > 0 else 0.0

    tot_cart_fmt = f"R$ {total_carteira:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    tot_div_fmt = f"R$ {total_dividendos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print(f"TOTAL DA CARTEIRA................: {tot_cart_fmt}")
    print(f"TOTAL DE DIVIDENDOS ESTIMADOS/MÊS.: {tot_div_fmt} (Yield Médio: {yield_medio_carteira:.2f}% a.m.)")
    print("=" * 90 + "\n")


def rodar_laboratorio_aportes(df):
    print("\n" + "=" * 55)
    print("         LABORATÓRIO DE APORTES INTELIGENTES")
    print("=" * 55)

    print("🔄 Atualizando cotações em tempo real do mercado...")
    try:
        df = gerar_dataframe_principal()
        print("✅ Cotações atualizadas com sucesso!")
    except Exception as e:
        print(f"⚠ Aviso: Não foi possível atualizar online ({e}). Usando base atual.")

    while True:
        try:
            entrada = input("\nQuanto você deseja aportar este mês? R$ ").strip().replace(".", "").replace(",", ".")
            valor_aporte = float(entrada)
            break
        except ValueError:
            print("❌ Valor inválido. Digite um número válido (ex: 950 ou 950,50).")

    if valor_aporte <= 0:
        print("❌ O valor do aporte precisa ser maior que zero.")
        return

    df['PREÇO ATUAL'] = pd.to_numeric(df['PREÇO ATUAL'], errors='coerce').fillna(0)
    df['DY ESPERADO'] = pd.to_numeric(df['DY ESPERADO'], errors='coerce').fillna(0)

    ativos_excluidos = ['BDIV11', 'JMBI11']
    df_analise = df[(df['PREÇO ATUAL'] > 0) & (~df['FII'].isin(ativos_excluidos))].copy()

    if df_analise.empty:
        print("❌ Nenhuma cotação disponível no momento para simular.")
        return

    df_analise['DY_ATUAL_PERC'] = (df_analise['DY ESPERADO'] / df_analise['PREÇO ATUAL']) * 100
    
    mask_vgia = df_analise['FII'] == 'VGIA11'
    if mask_vgia.any():
        df_analise.loc[mask_vgia, 'DY_ATUAL_PERC'] = (0.13 / 9.60) * 100

    df_top4 = df_analise.sort_values(by='DY_ATUAL_PERC', ascending=False).head(4)

    if len(df_top4) < 1:
        print("❌ Não há ativos suficientes para aplicar a regra de divisão.")
        return

    n_ativos = len(df_top4)
    alocacao_por_ativo = valor_aporte / n_ativos

    resultados = []
    total_gasto = 0.0

    for _, ativo in df_top4.iterrows():
        preco = float(ativo['PREÇO ATUAL'])
        qtd = int(alocacao_por_ativo // preco)
        gasto = qtd * preco
        resultados.append({
            "fii": ativo['FII'],
            "preco": preco,
            "qtd": qtd,
            "gasto": gasto,
            "dy": float(ativo['DY_ATUAL_PERC'])
        })
        total_gasto += gasto

    saldo_residual = valor_aporte - total_gasto

    resultados_ordenados = sorted(resultados, key=lambda x: x["dy"], reverse=True)
    
    indice_alvo = 0
    tentativas_sem_compra = 0
    max_tentativas = len(resultados_ordenados)

    while saldo_residual > 0 and tentativas_sem_compra < max_tentativas:
        item = resultados_ordenados[indice_alvo]
        if saldo_residual >= item["preco"]:
            item["qtd"] += 1
            item["gasto"] += item["preco"]
            saldo_residual -= item["preco"]
            total_gasto += item["preco"]
            tentativas_sem_compra = 0
        else:
            tentativas_sem_compra += 1
        
        indice_alvo = (indice_alvo + 1) % len(resultados_ordenados)

    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print("\n" + "-" * 55)
    print(f" SUGESTÃO DE COMPRA ({n_ativos} ATIVOS EX-BDIV/JMBI) - APORTE: {fmt_br(valor_aporte)}")
    print("-" * 55)
    
    for item in resultados:
        p_str = fmt_br(item['preco'])
        t_str = fmt_br(item['gasto'])
        print(f"Comprar {item['qtd']:>3} cotas de {item['fii']:<7} | Preço: {p_str:>9} | Total: {t_str:>11} (DY: {item['dy']:.2f}%)")
        
    print("-" * 55)
    print(f"Total utilizado......: {fmt_br(total_gasto)}")
    print(f"Troco/Saldo residual.: {fmt_br(saldo_residual)}")
    print("=" * 55 + "\n")

import os
import requests
import pandas as pd

import os
import requests
import pandas as pd
import yfinance as yf

# Token oficial da sua conta BRAPI
TOKEN_BRAPI = "qJH13J2kHzxkgBPcMy6STj"

import os
import requests
import pandas as pd
import yfinance as yf

# Token oficial da sua conta BRAPI
TOKEN_BRAPI = "qJH13J2kHzxkgBPcMy6STj"

def obter_historico_brapi(ticker):
    """
    Busca o histórico de dividendos via BRAPI (v2 Quote + Prime Dividends como contingência).
    """
    ticker_limpo = str(ticker).replace(".SA", "").strip().upper()
    
    # 1. TENTA PRIMEIRO ENDPOINT: STOCKS/QUOTE
    url_quote = f"https://brapi.dev/api/v2/stocks/quote?symbols={ticker_limpo}.SA&dividends=true&token={TOKEN_BRAPI}"
    historico_divs = []
    
    try:
        response = requests.get(url_quote, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            if dados.get("results"):
                historico_divs = dados["results"][0].get("dividendsData", {}).get("cashDividends", [])
    except Exception:
        pass

    # 2. CONTINGÊNCIA BRAPI: ENDPOINT DEDICADO DE DIVIDENDOS (caso o quote venha vazio)
    if not historico_divs:
        url_divs = f"https://brapi.dev/api/v2/prime/dividends?ticker={ticker_limpo}&token={TOKEN_BRAPI}"
        try:
            resp_div = requests.get(url_divs, timeout=10)
            if resp_div.status_code == 200:
                dados_div = resp_div.json()
                historico_divs = dados_div.get("results", [])
        except Exception:
            pass

    if not historico_divs:
        return pd.DataFrame()

    # Busca cotações no Yahoo para casar com as datas
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

    return pd.DataFrame()

def analisar_fii_historico(ticker, df_historico=None):
    """
    Análise avançada do histórico de dividendos com Volatilidade (CV),
    Estimativa de Data de Pagamento e Valuation Bazin FIIs.
    """
    ticker_upper = str(ticker).replace(".SA", "").strip().upper()

    # Busca os dados no módulo api_oasis
    df_analise = api_brapi(ticker_upper)

    if df_analise is None or df_analise.empty:
        print(f"\n⚠ Não foi possível obter o histórico para {ticker_upper}.")
        return

    # Normalização de datas e ordenação
    if 'Data_DT' not in df_analise.columns and 'Data COM' in df_analise.columns:
        df_analise['Data_DT'] = pd.to_datetime(df_analise['Data COM'], format='%d/%m/%Y', errors='coerce')
    
    if 'Data_DT' in df_analise.columns:
        df_analise['Ano'] = df_analise['Data_DT'].dt.year
        df_analise = df_analise.sort_values(by='Data_DT', ascending=False).reset_index(drop=True)

    # 1. ESTIMATIVA DE DATA PAGT QUANDO ESTIVER VAZIA OU COM HÍFEN
    for idx, row in df_analise.iterrows():
        dt_pag = str(row.get('Data Pagamento', '-')).strip()
        dt_com = row.get('Data_DT')

        if (dt_pag == '-' or dt_pag == 'nan' or not dt_pag) and pd.notnull(dt_com):
            # Regra prática de estimativa: ~25º dia corrido do mesmo mês
            ano_c, mes_c = dt_com.year, dt_com.month
            dia_est = 25 if mes_c != 2 else 28
            dt_est = pd.Timestamp(year=ano_c, month=mes_c, day=dia_est)
            df_analise.at[idx, 'Data Pagamento'] = dt_est.strftime('%d/%m/%Y*')  # Asterisco indica estimado

    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print("\n" + "=" * 95)
    print(f"                     HISTÓRICO DE DIVIDEND YIELD REAL: {ticker_upper}")
    print("=" * 95)
    print(f"{'Mês/Ano':<10} | {'FII':<7} | {'Data COM':<12} | {'Data PAGT':<12} | {'DY (R$)':<10} | {'Cot. COM':<10} | {'Yield (%)':<8}")
    print("-" * 95)

    for _, linha in df_analise.iterrows():
        mes_ano = linha.get('Mês/Ano', '-')
        dt_com = linha.get('Data COM', '-')
        dt_pag = linha.get('Data Pagamento', '-')
        dy_val = float(linha.get('DY', 0.0))
        cot_com = float(linha.get('Preço', 0.0))
        yield_pct = float(linha.get('Yield (%)', 0.0))

        print(f"{mes_ano:<10} | {ticker_upper:<7} | {dt_com:<12} | {dt_pag:<12} | {fmt_br(dy_val):>10} | {fmt_br(cot_com):>10} | {yield_pct:>7.2f}%")
    
    print("-" * 95)
    print("  * Data Pagamento estimada com base no ciclo padrão do ativo (25º dia).")

    # 2. RESUMO CONSOLIDADO POR ANO + VOLATILIDADE (CV)
    if 'Ano' in df_analise.columns:
        print("\n" + "=" * 70)
        print("          RESUMO CONSOLIDADO & VOLATILIDADE POR ANO")
        print("=" * 70)
        print(f"{'Ano':<8} | {'Média DY':<12} | {'Preço Médio':<14} | {'Yield (%)':<8} | {'Volatilidade (CV)':<18}")
        print("-" * 70)

        # Agrupamento anual calculando Média e Desvio Padrão dos proventos
        anos = sorted(df_analise['Ano'].unique(), reverse=True)
        for ano in anos:
            df_ano = df_analise[df_analise['Ano'] == ano]
            dy_m = df_ano['DY'].mean()
            pr_m = df_ano['Preço'].mean()
            dy_std = df_ano['DY'].std()

            y_m = (dy_m / pr_m * 100) if pr_m > 0 else 0.0
            
            # Coeficiente de Variação = (Desvio Padrão / Média) * 100
            if dy_m > 0 and pd.notnull(dy_std):
                cv_pct = (dy_std / dy_m) * 100
                if cv_pct <= 10:
                    status_cv = f"Baixa ({cv_pct:.1f}%) 🟢"
                elif cv_pct <= 25:
                    status_cv = f"Média ({cv_pct:.1f}%) 🟡"
                else:
                    status_cv = f"Alta ({cv_pct:.1f}%) 🔴"
            else:
                status_cv = "Estável (0%) 🟢"

            print(f"{ano:<8} | {fmt_br(dy_m):>12} | {fmt_br(pr_m):>14} | {y_m:>7.2f}%  | {status_cv:<18}")

        print("=" * 70)

    # 3. VALUATION BAZIN (ÚLTIMOS 12 MESES) - CORRIGIDO
    ultimos_12m = df_analise.head(12)
    if not ultimos_12m.empty:
        media_12m = ultimos_12m['DY'].mean()
        soma_12m = ultimos_12m['DY'].sum()
        cotacao_atual = ultimos_12m.iloc[0]['Preço']

        # Taxa de Desconto Bazin FIIs = 0,6% ao mês (7,2% ao ano)
        precos_teto = media_12m / 0.006

        if cotacao_atual > 0 and precos_teto > 0:
            if cotacao_atual <= precos_teto:
                # Desconto Real sobre o Teto: (1 - Preço Atual / Preço Teto) * 100
                desconto = (1 - (cotacao_atual / precos_teto)) * 100
                status_teto = f"🟢 COMPRA EVIDENTE (Desconto de {desconto:.1f}%)"
            else:
                # Ágio sobre o Teto: (Preço Atual / Preço Teto - 1) * 100
                agio = ((cotacao_atual / precos_teto) - 1) * 100
                status_teto = f"🔴 ACIMA DO TETO (Ágio de {agio:.1f}%)"
        else:
            status_teto = "N/D"

        print("\n" + "=" * 70)
        print("          INSIGHTS DE VALUATION & PREÇO TETO (BAZIN FIIs)")
        print("=" * 70)
        print(f" Provento Médio Móvel (12m) : {fmt_br(media_12m)} /mês  (Total: {fmt_br(soma_12m)})")
        print(f" Cotação de Referência       : {fmt_br(cotacao_atual)}")
        print(f" Preço Teto Bazin (0,6% a.m.): {fmt_br(precos_teto)}")
        print(f" Status do Preço             : {status_teto}")
        print("=" * 70 + "\n")

    # Exportação para Excel
    try:
        pasta_dados = "Dados"
        if not os.path.exists(pasta_dados):
            os.makedirs(pasta_dados)
        path_out = os.path.join(pasta_dados, f"Historico_DY_{ticker_upper}.xlsx")
        
        df_export = df_analise.drop(columns=['Data_DT'], errors='ignore')
        df_export.to_excel(path_out, index=False)
        print(f"✅ Análise exportada com sucesso para: {path_out}\n")
    except Exception:
        pass

def rodar_simulacao_oasis(df, PASTA_DADOS="Dados"):
    print("\n" + "=" * 55)
    print("           PROJEÇÃO PATRIMONIAL - OASIS 2035")
    print("=" * 55)
     
    df_carteira = df[df['QUANTIDADE'] > 0].copy()
    df_carteira['QUANTIDADE'] = pd.to_numeric(df_carteira['QUANTIDADE'], errors='coerce').fillna(0)
    df_carteira['PREÇO ATUAL'] = pd.to_numeric(df_carteira['PREÇO ATUAL'], errors='coerce').fillna(0)
    
    patrimonio_atual = (df_carteira['QUANTIDADE'] * df_carteira['PREÇO ATUAL']).sum()
     
    df_mercado = df[df['PREÇO ATUAL'] > 0].copy()
    df_mercado['DY ESPERADO'] = pd.to_numeric(df_mercado['DY ESPERADO'], errors='coerce').fillna(0)
    df_mercado['PREÇO ATUAL'] = pd.to_numeric(df_mercado['PREÇO ATUAL'], errors='coerce').fillna(0)
    
    df_mercado['DY_PERC'] = (df_mercado['DY ESPERADO'] / df_mercado['PREÇO ATUAL'])
    yield_medio_radar = df_mercado['DY_PERC'].mean()
     
    if pd.isna(yield_medio_radar) or yield_medio_radar == 0:
        yield_medio_radar = 0.011

    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print(f"Patrimônio Atual em FIIs: {fmt_br(patrimonio_atual)}")
    print(f"Taxa Cenário Base:         {yield_medio_radar * 100:.2f}% ao mês")
    
    yield_estressado = yield_medio_radar * 0.85
    print(f"Taxa Cenário Crise (-15%): {yield_estressado * 100:.2f}% ao mês")
    
    try:
        aporte_input = input("\nDigite o valor do seu aporte mensal: R$ ").replace(".", "").replace(",", ".")
        aporte_mensal = float(aporte_input)
    except ValueError:
        print("❌ Valor inválido. Retornando ao menu.")
        return
         
    data_atual = pd.Timestamp.now()
    data_alvo = pd.Timestamp(2035, 9, 1)
    meses_restantes = (data_alvo.year - data_atual.year) * 12 + (data_alvo.month - data_atual.month)
     
    if meses_restantes <= 0:
        print("⚠ O prazo limite de setembro de 2035 já foi atingido.")
        return
         
    print(f"\nPrazo: {meses_restantes} meses | Reinvestimento Total Ativado.")
     
    pat_final_base, hist_base, pat_final_crise, hist_crise = rodar_calculo_cenarios(
        patrimonio_atual, yield_medio_radar, aporte_mensal, meses_restantes, data_atual
    )     
    
    df_base = pd.DataFrame(hist_base)
    df_crise = pd.DataFrame(hist_crise)
     
    renda_final_base = pat_final_base * yield_medio_radar
    total_aportado = aporte_mensal * meses_restantes
     
    print("\n" + "=" * 55)
    print("      [TELA 1] CENÁRIO BASE - RADAR ATUAL")
    print("=" * 55)
    print(f"Patrimônio Alvo Final:   {fmt_br(pat_final_base)}")
    print(f"Renda Mensal Estimada:   {fmt_br(renda_final_base)} / mês")
    print(f"Seu bolso (Aportes):     {fmt_br(total_aportado)}")
    print(f"Efeito do Mercado:       {fmt_br(pat_final_base - patrimonio_atual - total_aportado)}")
    print("-" * 55)
    print("Últimos 3 meses (Base):")
    for _, reg in df_base.tail(3).iterrows():
        p_f = fmt_br(reg['Patrimônio Final'])
        d_r = fmt_br(reg['Dividendos Recebidos'])
        print(f"  {reg['Mês/Ano']}: Pat: {p_f:>15} | Rend: {d_r:>12}")
         
    renda_final_crise = pat_final_crise * yield_estressado
     
    print("\n" + "=" * 55)
    print("   [TELA 2] TESTE DE ESTRESSE - CONSERVADOR (-15%)")
    print("=" * 55)
    print(f"Patrimônio Alvo Final:   {fmt_br(pat_final_crise)}")
    print(f"Renda Mensal Estimada:   {fmt_br(renda_final_crise)} / mês")
    print(f"Seu bolso (Aportes):     {fmt_br(total_aportado)}")
    print(f"Efeito do Mercado:       {fmt_br(pat_final_crise - patrimonio_atual - total_aportado)}")
    print("-" * 55)
    print("Últimos 3 meses (Crise):")
    for _, reg in df_crise.tail(3).iterrows():
        p_fc = fmt_br(reg['Patrimônio Final'])
        d_rc = fmt_br(reg['Dividendos Recebidos'])
        print(f"  {reg['Mês/Ano']}: Pat: {p_fc:>15} | Rend: {d_rc:>12}")
    print("=" * 55)
     
    try:
        if not os.path.exists(PASTA_DADOS):
            os.makedirs(PASTA_DADOS)
            
        nome_arquivo = os.path.join(PASTA_DADOS, "Simulacao_Oasis_Comparativa.xlsx")
        
        with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
            df_base.to_excel(writer, sheet_name='Cenário Base', index=False)
            df_crise.to_excel(writer, sheet_name='Cenário Crise -15%', index=False)
            
        print(f"\n📊 Planilha comparativa com as duas abas salva em: {nome_arquivo}\n")
    except Exception as e:
        print(f"\n❌ Erro ao salvar o Excel: {e}\n")


def gerar_relatorio_executivo(df):
    data_atual = pd.Timestamp.now()
    df_carteira = df[df['QUANTIDADE'] > 0].copy()
    
    div_estimado_lista = []
    dy_unitario_mensal_lista = []
    
    for _, linha in df_carteira.iterrows():
        fii = str(linha['FII']).strip().upper()
        dy_bruto = float(linha['DY ESPERADO'])
        qtde = int(linha['QUANTIDADE'])

        if fii == 'BDIV11':
            dy_mensal = dy_bruto / 3
        else:
            dy_mensal = dy_bruto

        renda_fii = dy_mensal * qtde
        div_estimado_lista.append(renda_fii)
        dy_unitario_mensal_lista.append(dy_mensal)

    df_carteira['DY_UNITARIO_MENSAL'] = dy_unitario_mensal_lista
    df_carteira['DIV_ESTIMADO'] = div_estimado_lista
    df_carteira['TOTAL_INVESTIDO'] = df_carteira['QUANTIDADE'] * df_carteira['PREÇO ATUAL']
    
    patrimonio_atual = df_carteira['TOTAL_INVESTIDO'].sum()

    df_mercado = df[df['PREÇO ATUAL'] > 0].copy()
    df_mercado['DY_PERC'] = (df_mercado['DY ESPERADO'] / df_mercado['PREÇO ATUAL'])
    yield_medio_radar = df_mercado['DY_PERC'].mean()
    if pd.isna(yield_medio_radar) or yield_medio_radar == 0:
        yield_medio_radar = 0.011

    dividendos_mensais_atuais = df_carteira['DIV_ESTIMADO'].sum()
    total_ativos = len(df_carteira)

    try:
        exportar_relatorio_executivo(
            df, data_atual, patrimonio_atual, yield_medio_radar,
            dividendos_mensais_atuais, total_ativos, df_carteira
        )
        registrar("Relatório executivo gerado com sucesso.")
    except Exception as e:
        print(f"\n❌ Erro ao exportar o relatório executivo: {e}")


def exibir_historico_carteira(df):
    processar_historico_carteira(df, PASTA_DADOS)

def buscar_dados_brapi(ticker):
    return api_brapi(ticker)

def buscar_dados_yahoo(ticker):
    return api_yahoo(ticker)


def menu():
    print("=============================================")
    print("                  FII CONTROL")
    print("=============================================")
    print("1 - Atualizar cotações")
    print("2 - Mostrar carteira")
    print("3 - Histórico de Dividendos (Data COM/PAGT)")
    print("4 - Laboratório")
    print("5 - Comparar FIIs")
    print("6 - Simulações")
    print("7 - Relatórios")
    print("8 - Radar Ações (Bazin)")
    print("9 - Gerenciar Carteira FII (Adicionar/Remover)")
    print("0 - Sair")
    print()
    return input("Escolha uma opção: ")


if __name__ == "__main__":
    registrar("OASIS iniciado.")
    print("=============================================")
    print("      INICIALIZANDO MOTOR OASIS 2035")
    print("=============================================")
    print("Buscando dados em tempo real (BRAPI + Hybrid)...")
    df_oasis = gerar_dataframe_principal()

    if df_oasis is not None:
        for indice, linha in df_oasis.iterrows():
            df_oasis.loc[indice, "NOTA OASIS"] = calcular_nota(linha)
        mostrar_painel_oasis(df_oasis)

    while True:
        opcao = menu()

        if opcao == "1":
            print("\nAtualizando dados em tempo real...")
            df_oasis = gerar_dataframe_principal()
            mostrar_painel_oasis(df_oasis)

        elif opcao == "2":
            df_oasis = gerar_dataframe_principal()
            mostrar_painel_oasis(df_oasis)

        elif opcao == "3":
            ticker_busca = input("\nDigite o Ticker do FII para analisar o histórico (ex: JMBI11): ").strip().upper()
            analisar_fii_historico(ticker_busca, df_oasis)
       
        elif opcao == "4":
            print("\n==========================================================")
            print("         LABORATÓRIO DE APORTES INTELIGENTES")
            print("==========================================================")
            print("🔄 Atualizando cotações em tempo real do mercado...")
            
            try:
                if 'cotacoes' in globals() and hasattr(cotacoes, 'atualizar_cotacoes'):
                    cotacoes.atualizar_cotacoes(df_carteira)
                print("✅ Cotações atualizadas com sucesso!\n")
            except Exception:
                print("⚠️ Cotações mantidas com base na última leitura.\n")

            # 1. Entrada de capital do usuário
            try:
                entrada_str = input("Quanto você deseja aportar este mês? R$ ").strip().replace(",", ".")
                aporte_disponivel = float(entrada_str) if entrada_str else 2500.0
            except ValueError:
                print("❌ Valor inválido. Assumindo R$ 2500,00 como padrão.")
                aporte_disponivel = 2500.0

            lista_dados_completos = []
            tickers_painel = ["BDIV11", "JMBI11", "VGIA11", "VGIR11", "SNAG11", "VHFA11"]

            for t in tickers_painel:
                p_atual = 0.0
                provento = 0.0
                cotas = 100
                pm_orig = 0.0
                div_rec = 0.0

                if 'df_carteira' in locals() and df_carteira is not None and not df_carteira.empty:
                    item = df_carteira[df_carteira['FII'].astype(str).str.upper() == t]
                    if not item.empty:
                        row = item.iloc[0]
                        p_atual = float(row.get('PREÇO ATUAL', 0.0))
                        provento = float(row.get('DY ESPERADO', 0.0))
                        cotas = int(row.get('QUANTIDADE', 100))
                        pm_orig = float(row.get('PREÇO MÉDIO', p_atual))
                        div_rec = float(row.get('DIVIDENDOS_ACUMULADOS', 0.0))

                # CORREÇÃO 1: Ajustado preço fallback do BDIV11 para o preço real recalibrado (R$ 36.60)
                dados_fallback = {
                    "BDIV11": {"p": 36.60, "prov": 0.280, "pm": 36.60, "div": 30.0, "dia": 23, "meses": [1, 4, 7, 10]},
                    "JMBI11": {"p": 84.70, "prov": 0.900, "pm": 83.66, "div": 20.0, "dia": 15, "meses": None},
                    "VGIA11": {"p": 8.45, "prov": 0.110, "pm": 9.20, "div": 120.0, "dia": 10, "meses": None},
                    "VGIR11": {"p": 9.39, "prov": 0.110, "pm": 9.80, "div": 34.0, "dia": 10, "meses": None},
                    "SNAG11": {"p": 9.80, "prov": 0.105, "pm": 10.05, "div": 47.0, "dia": 15, "meses": None},
                    "VHFA11": {"p": 10.86, "prov": 0.090, "pm": 9.80, "div": 25.0, "dia": 7, "meses": None},
                }

                fb = dados_fallback.get(t, {"p": 10.0, "prov": 0.10, "pm": 10.0, "div": 0.0, "dia": 15, "meses": None})

                p_final = p_atual if p_atual > 0 else fb["p"]
                prov_final = provento if provento > 0 else fb["prov"]
                pm_final = pm_orig if pm_orig > 0 else fb["pm"]
                div_final = div_rec if div_rec > 0 else fb["div"]

                prov_mensal = (prov_final / 3.0) if t == "BDIV11" and prov_final > 0.20 else prov_final
                prov_12m = prov_final * 4 if t == "BDIV11" else prov_final * 12

                dados_fii = {
                    "ticker": t,
                    "preco_atual": p_final,
                    "ultimo_provento": prov_mensal,
                    "provento_12m": prov_12m,
                    "cotas": max(1, cotas),
                    "preco_medio_original": pm_final,
                    "total_dividendos_recebidos": div_final,
                    "dia_padrao_data_com": fb["dia"],
                    "meses": fb["meses"]
                }

                metricas_calculadas = calcular_laboratorio_oasis(dados_fii)
                dados_fii.update(metricas_calculadas)
                lista_dados_completos.append(dados_fii)

            ativos_elegiveis = [f for f in lista_dados_completos if f.get("spread", 0) > 0 and f["ticker"] not in ["BDIV11", "JMBI11"]]

            if not ativos_elegiveis:
                ativos_elegiveis = [f for f in lista_dados_completos if f["ticker"] not in ["BDIV11", "JMBI11"]]

            soma_spreads = sum(f.get("spread", 0) for f in ativos_elegiveis)

            # --- ALOCAÇÃO INICIAL ---
            sugestoes_compra = {}
            total_gasto = 0.0

            for f in lista_dados_completos:
                ticker = f["ticker"]
                spread_val = f.get("spread", 0.0)

                if ticker in ["BDIV11", "JMBI11"] or spread_val <= 0:
                    sugestoes_compra[ticker] = 0
                    continue

                proporcao_fundo = spread_val / soma_spreads if soma_spreads > 0 else 0
                capital_destinado = aporte_disponivel * proporcao_fundo
                qtd_cotas = int(capital_destinado // f["preco_atual"])
                
                sugestoes_compra[ticker] = qtd_cotas
                total_gasto += qtd_cotas * f["preco_atual"]

            # CORREÇÃO 2: LOOP VARRE-SOBRAS (Otimização do Troco)
            # Tenta encaixar cotas extras com a sobra do caixa priorizando o maior spread
            saldo_residual = aporte_disponivel - total_gasto
            ativos_para_sobra = sorted(ativos_elegiveis, key=lambda x: x.get("spread", 0), reverse=True)
            
            houve_compra_sobra = True
            while houve_compra_sobra:
                houve_compra_sobra = False
                for f in ativos_para_sobra:
                    ticker = f["ticker"]
                    preco = f["preco_atual"]
                    if saldo_residual >= preco:
                        sugestoes_compra[ticker] += 1
                        total_gasto += preco
                        saldo_residual -= preco
                        houve_compra_sobra = True
                        break  # Recomeça a varredura do maior spread para o menor

            # --- EXIBIÇÃO DA SUGESTÃO NA TELA ---
            p_fmt_aporte = f"R$ {aporte_disponivel:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            print("----------------------------------------------------------")
            print(f"SUGESTÃO DE COMPRA DINÂMICA (EX-BDIV/JMBI) - APORTE: {p_fmt_aporte}")
            print("----------------------------------------------------------\n")

            for f in lista_dados_completos:
                ticker = f["ticker"]
                spread_val = f.get("spread", 0.0)
                qtd_cotas = sugestoes_compra[ticker]
                custo_total_ativo = qtd_cotas * f["preco_atual"]
                p_atual_fmt = f"R$ {f['preco_atual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                tot_fmt = f"R$ {custo_total_ativo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                if ticker == "BDIV11":
                    print(f"Comprar   0 cotas de {ticker:<6} | Preço: {p_atual_fmt:>10} | Total: R$       0,00 (Spread: {spread_val:>+5.1f}% 🛑 QUALIFICADO)")
                elif ticker == "JMBI11":
                    print(f"Comprar   0 cotas de {ticker:<6} | Preço: {p_atual_fmt:>10} | Total: R$       0,00 (🔒 TETO DIVERSIFICAÇÃO)")
                elif spread_val <= 0:
                    print(f"Comprar   0 cotas de {ticker:<6} | Preço: {p_atual_fmt:>10} | Total: R$       0,00 (Spread: {spread_val:>+5.1f}% ⚠️ QUARENTENA)")
                else:
                    dy_mensal_tela = (f["ultimo_provento"] / f["preco_atual"]) * 100 if f["preco_atual"] > 0 else 0.0
                    print(f"Comprar {qtd_cotas:>3} cotas de {ticker:<6} | Preço: {p_atual_fmt:>10} | Total: {tot_fmt:>10} (DY: {dy_mensal_tela:.2f}%)")

            tot_util_fmt = f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            troco_fmt = f"R$ {saldo_residual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            print("\n----------------------------------------------------------")
            print(f"Total utilizado......: {tot_util_fmt}")
            print(f"Troco/Saldo residual.: {troco_fmt}")
            print("==========================================================\n")

            # 3. EXIBIÇÃO DA TABELA ANALÍTICA CORRIGIDA
            print("========================================================================================================")
            print("                                LABORATÓRIO OÁSIS 2035 - MÉTRICAS EXTREMAS")
            print("========================================================================================================")
            print("MÉTRICA AVANÇADA          |  " + "    |  ".join(tickers_painel) + "    ")
            print("--------------------------------------------------------------------------------------------------------")
            print("P.Médio Amortizado        | " + " | ".join([f"  R$ {f.get('pm_amortizado', 0.0):>5.2f}".replace('.', ',') for f in lista_dados_completos]))
            print("YoC Mensal (S/ PM Amort.) | " + " | ".join([f"{f.get('yoc_mensal', 0.0):>8.2f}%".replace('.', ',') for f in lista_dados_completos]))
            print("Spread vs IPCA+ 2035      | " + " | ".join([f"{f.get('spread', 0.0):>+8.1f}%".replace('.', ',') for f in lista_dados_completos]))
            print("Gatilho Data COM          | " + " | ".join([f"Faltam {f.get('dias_data_com', 0):>3}d" for f in lista_dados_completos]))
            print("Eficiência Fiscal         | " + " | ".join(["   100% 🟢 " for _ in tickers_painel]))
            print("========================================================================================================")
        elif opcao == "5":
            print("\n" + "=" * 55)
            print("                 COMPARADOR DE FIIs")
            print("=" * 55)
            fii1_input = input("Primeiro FII (ex: VGIA11): ").strip().upper()
            fii2_input = input("Segundo FII  (ex: SNAG11): ").strip().upper()
            comparar_fiis(fii1_input, fii2_input, df_oasis, modulo_cotacoes=cotacoes)

        elif opcao == "6":
            rodar_simulacao_oasis(df_oasis)

        elif opcao == "7":
            gerar_relatorio_executivo(df_oasis)

        elif opcao == "8":
            menu_radar_acoes()

        elif opcao == "9":
            menu_gerenciar_fiis()

        elif opcao == "0":
            print("\nAté logo, Adilson! Bons investimentos rumo a 2035.")
            import sys
            sys.exit(0)

        else:
            print(f"\nOpção '{opcao}' inválida. Tente novamente.")
