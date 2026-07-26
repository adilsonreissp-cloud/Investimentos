import os
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

# ou 'import comparador', dependendo de como estruturou
PASTA_DADOS = "Dados"

import os
import pandas as pd

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

        # O DY ESPERADO do ativos.csv já está cadastrado como valor mensal em R$ por cota
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
import pandas as pd

def rodar_laboratorio_aportes(df):
    print("\n" + "=" * 55)
    print("         LABORATÓRIO DE APORTES INTELIGENTES")
    print("=" * 55)

    print("🔄 Atualizando cotações em tempo real do mercado...")
    try:
        # Se existir a função de geração principal, atualiza a base
        df = gerar_dataframe_principal()
        print("✅ Cotações atualizadas com sucesso!")
    except Exception as e:
        print(f"⚠ Aviso: Não foi possível atualizar online ({e}). Usando base atual.")

    # Loop para entrada de valor com suporte a vírgula
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

    # Garantia de tipos numéricos defensivos
    df['PREÇO ATUAL'] = pd.to_numeric(df['PREÇO ATUAL'], errors='coerce').fillna(0)
    df['DY ESPERADO'] = pd.to_numeric(df['DY ESPERADO'], errors='coerce').fillna(0)

    # 🔒 TRAVA ESTRATÉGICA: Ignora BDIV11 e JMBI11 para focar no rebalanceamento dos 4 menores
    ativos_excluidos = ['BDIV11', 'JMBI11']
    df_analise = df[(df['PREÇO ATUAL'] > 0) & (~df['FII'].isin(ativos_excluidos))].copy()

    if df_analise.empty:
        print("❌ Nenhuma cotação disponível no momento para simular.")
        return

    # Cálculo do Dividend Yield mensal percentual
    df_analise['DY_ATUAL_PERC'] = (df_analise['DY ESPERADO'] / df_analise['PREÇO ATUAL']) * 100
    
    # Regra de Exceção para VGIA11 (Ajuste pontual de Yield se presente)
    mask_vgia = df_analise['FII'] == 'VGIA11'
    if mask_vgia.any():
        df_analise.loc[mask_vgia, 'DY_ATUAL_PERC'] = (0.13 / 9.60) * 100

    # Seleção dos Top 4 ativos filtrados
    df_top4 = df_analise.sort_values(by='DY_ATUAL_PERC', ascending=False).head(4)

    if len(df_top4) < 1:
        print("❌ Não há ativos suficientes para aplicar a regra de divisão.")
        return

    n_ativos = len(df_top4)
    alocacao_por_ativo = valor_aporte / n_ativos

    resultados = []
    total_gasto = 0.0

    # 1ª Passada: Compra de cotas base por cotação de cada ativo
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

    # 2ª Passada: Varredura de troco priorizando os maiores Yields
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

    # Lambda de formatação padrão BR para tela
    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Exibição dos resultados formatados
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
def analisar_fii_historico(ticker, df_historico):
    if df_historico is None or df_historico.empty:
        print(f"\n⚠ Erro: Não foram encontrados dividendos ou dados históricos para {ticker}.")
        return

    df_analise = df_historico.copy()

    # Tratamento de Datas
    if 'Data' in df_analise.columns:
        df_analise['Data_DT'] = pd.to_datetime(df_analise['Data'])
    elif 'Data COM' in df_analise.columns:
        df_analise['Data_DT'] = pd.to_datetime(df_analise['Data COM'], format='%d/%m/%Y', errors='coerce')
    else:
        try:
            df_analise['Data_DT'] = pd.to_datetime(df_analise.index)
        except:
            df_analise['Data_DT'] = pd.Timestamp.now()

    df_analise['Ano'] = df_analise['Data_DT'].dt.year

    # Regra de Negócio para o BDIV11 (Trimestral -> Mensal)
    ticker_upper = str(ticker).strip().upper()
    if ticker_upper == "BDIV11" and 'DY' in df_analise.columns:
        df_analise['DY'] = df_analise['DY'] / 3.0
        if 'Yield' in df_analise.columns:
            df_analise['Yield'] = df_analise['Yield'] / 3.0

    print("\n" + "=" * 55)
    print(f"               ANÁLISE HISTÓRICA: {ticker_upper}")
    print("=" * 55)

    preco_min = f"R$ {df_analise['Preço'].min():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    preco_max = f"R$ {df_analise['Preço'].max():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    preco_med = f"R$ {df_analise['Preço'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    dy_med = f"R$ {df_analise['DY'].mean():,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    dy_min = f"R$ {df_analise['DY'].min():,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    dy_max = f"R$ {df_analise['DY'].max():,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

    yield_geral = df_analise['Yield'].mean()
    yield_geral_val = yield_geral if yield_geral > 1 else yield_geral * 100
    yield_geral_fmt = f"{yield_geral_val:.2f}%".replace(".", ",")

    print(f"Cotação mínima........ {preco_min}")
    print(f"Cotação máxima........ {preco_max}")
    print(f"Cotação média......... {preco_med}")
    print(f"DY mensal médio....... {dy_med}")
    print(f"Menor DY mensal....... {dy_min}")
    print(f"Maior DY mensal....... {dy_max}")
    print(f"Yield mensal médio.... {yield_geral_fmt}")
    print(f"Registros analisados.. {len(df_analise)}")
    print("=" * 55)

    print("\nResumo das Médias por Ano (Evita distorção de Desdobramentos):")
    print(f"{'Ano':<6} | {'Média Preço':<14} | {'Média DY Mês':<14} | {'Yield Mês':<10}")
    print("-" * 55)

    resumo_anual = df_analise.groupby('Ano').agg({
        'Preço': 'mean',
        'DY': 'mean',
        'Yield': 'mean'
    }).sort_index(ascending=False)

    for ano, linha in resumo_anual.iterrows():
        p_ano = f"R$ {linha['Preço']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        dy_ano = f"R$ {linha['DY']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        y_anual_val = linha['Yield'] if linha['Yield'] > 1 else linha['Yield'] * 100
        y_ano_fmt = f"{y_anual_val:.2f}%".replace(".", ",")

        print(f"{ano:<6} | {p_ano:>14} | {dy_ano:>14} | {y_ano_fmt:>10}")

    print("-" * 55)
    print("\nHistórico de Distribuição Mensal:")
    print(f"{'Data COM':<12} | {'Preço':<10} | {'DY Mês':<10} | {'Yield':<8}")
    print("-" * 55)

    for _, linha in df_analise.iterrows():
        data_formatada = linha['Data_DT'].strftime('%d/%m/%Y')
        p_linha = f"R$ {linha['Preço']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        dy_linha = f"R$ {linha['DY']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        y_val = linha['Yield'] if linha['Yield'] > 1 else linha['Yield'] * 100
        y_fmt = f"{y_val:.2f}%".replace(".", ",")

        print(f"{data_formatada:<12} | {p_linha:>10} | {dy_linha:>10} | {y_fmt:>8}")

    print("-" * 55)
    print(f"Yield médio do período: {yield_geral_fmt}")

    # GERAÇÃO DA PLANILHA EXCEL LIMPA E FORMATADA
    try:
        PASTA_DADOS = "Dados"
        if not os.path.exists(PASTA_DADOS):
            os.makedirs(PASTA_DADOS)

        # Monta DataFrame específico para exportação Excel
        df_excel = pd.DataFrame()
        df_excel['Data COM'] = df_analise['Data_DT'].dt.strftime('%d/%m/%Y')
        df_excel['Ano'] = df_analise['Ano']
        df_excel['Preço'] = df_analise['Preço'].round(2)
        df_excel['DY Mês'] = df_analise['DY'].round(4)

        # Ajusta Yield em %
        df_excel['Yield (%)'] = df_analise['Yield'].apply(lambda x: round(x * 100 if x <= 1 else x, 2))

        pasta_analise = os.path.join(PASTA_DADOS, f"Analise_{ticker_upper}.xlsx")
        df_excel.to_excel(pasta_analise, index=False)
        print(f"\n✅ Análise limpa e formatada salva com sucesso em: {pasta_analise}")
    except Exception as e:
        print(f"\nAviso: Não foi possível gerar a planilha Excel: {e}")
    print("=" * 55 + "\n")

import os
import pandas as pd
import pandas as pd

def rodar_calculo_cenarios(patrimonio_inicial, yield_mensal, aporte_mensal, meses, data_inicial):
    """
    Executa a projeção mês a mês com reinvestimento de dividendos e aportes.
    Retorna o patrimônio final e o histórico em lista de dicionários.
    """
    # 1. Cenário Base
    patrimonio_base = patrimonio_inicial
    historico_base = []
    
    for m in range(1, meses + 1):
        data_mes = data_inicial + pd.DateOffset(months=m)
        rotulo_data = data_mes.strftime("%m/%Y")
        
        # Rendimento gerado pelo patrimônio no início do mês
        dividendos = patrimonio_base * yield_mensal
        
        # Reinvestimento dos dividendos + Aporte do mês
        patrimonio_base += dividendos + aporte_mensal
        
        historico_base.append({
            'Mês/Ano': rotulo_data,
            'Patrimônio Final': patrimonio_base,
            'Dividendos Recebidos': dividendos,
            'Aporte Mês': aporte_mensal
        })
        
    pat_final_base = patrimonio_base

    # 2. Cenário de Crise (-15% no Yield)
    yield_crise = yield_mensal * 0.85
    patrimonio_crise = patrimonio_inicial
    historico_crise = []
    
    for m in range(1, meses + 1):
        data_mes = data_inicial + pd.DateOffset(months=m)
        rotulo_data = data_mes.strftime("%m/%Y")
        
        dividendos_crise = patrimonio_crise * yield_crise
        patrimonio_crise += dividendos_crise + aporte_mensal
        
        historico_crise.append({
            'Mês/Ano': rotulo_data,
            'Patrimônio Final': patrimonio_crise,
            'Dividendos Recebidos': dividendos_crise,
            'Aporte Mês': aporte_mensal
        })
        
    pat_final_crise = patrimonio_crise

    return pat_final_base, historico_base, pat_final_crise, historico_crise
    
def rodar_simulacao_oasis(df, PASTA_DADOS="Dados"):
    print("\n" + "=" * 55)
    print("           PROJEÇÃO PATRIMONIAL - OASIS 2035")
    print("=" * 55)
     
    # Tratamento defensivo de colunas e tipos
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

    # Função auxiliar interna de formatação BR
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
     
    # Executa a função de cálculo dos cenários
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
     
    # Exportação para o Excel
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
    print("3 - Histórico")
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
            analisar_historico_fii(df_oasis)
        elif opcao == "4":
            rodar_laboratorio_aportes(df_oasis)
        elif opcao == "5":
            print("\n" + "=" * 55)
            print("                COMPARADOR DE FIIs")
            print("=" * 55)
            
            fii1_input = input("Primeiro FII (ex: VGIA11): ").strip()
            fii2_input = input("Segundo FII  (ex: SNAG11): ").strip()
            
            # Passamos 'cotacoes' ou 'api_oasis' para buscar FIIs fora da carteira
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
            break
        else:
            print(f"\nOpção '{opcao}' inválida. Tente novamente.")
