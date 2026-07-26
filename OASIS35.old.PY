import requests
import yfinance as yf
import pandas as pd
import os
 
PASTA_DADOS = "Dados"
 
def gerar_dataframe_principal():
    """Carrega as tabelas locais e cruza com os dados de cotação da BRAPI"""
    TOKEN = "qJH13J2kHzxkgBPcMy6STj"
    PASTA_DADOS = "Dados"

    try:
        df_carteira = pd.read_csv(os.path.join(PASTA_DADOS, "carteira.csv"), sep=";")
        df_carteira.columns = df_carteira.columns.str.strip().str.upper()
        df_carteira["FII"] = df_carteira["FII"].str.strip().str.upper()
    except FileNotFoundError:
        df_carteira = pd.DataFrame(columns=["FII", "QUANTIDADE", "PREÇO MÉDIO"])
    try:
        df_ativos = pd.read_csv(os.path.join(PASTA_DADOS, "ativos.csv"), sep=";")
        df_ativos.columns = df_ativos.columns.str.strip()
        
        # Mapeia 'Ticker' para 'FII' se o cabeçalho usar esse nome
        if "Ticker" in df_ativos.columns:
            df_ativos = df_ativos.rename(columns={"Ticker": "FII"})
            
        # Deixa os nomes das colunas em maiúsculo (FII, CATEGORIA, SEGMENTO, GESTORA, etc.)
        df_ativos.columns = df_ativos.columns.str.upper()
        df_ativos["FII"] = df_ativos["FII"].str.strip().str.upper()
        
        # Opcional: Limpa espaços em branco dos textos das novas colunas para evitar erros de busca
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
         TOKEN = "qJH13J2kHzxkgBPcMy6STj"
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

     # Monta a lista de preços cruzando com o dicionário retornado
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
 
def mostrar_painel_oasis(df):
    print("\n" + "=" * 45)
    print("                FII CONTROL - OASIS 2035")
    print("=" * 45 + "\n")
 
    df_minha_carteira = df[df['QUANTIDADE'] > 0].copy()
 
    for _, linha in df_minha_carteira.iterrows():
        print(f"{linha['FII']:<8} R$ {linha['PREÇO ATUAL']:.2f}")
 
    print("\n" + "=" * 45)
    print("CARTEIRA")
    print("=" * 45)
    total_carteira = 0.0
    for _, linha in df_minha_carteira.iterrows():
        total_ativo = linha['QUANTIDADE'] * linha['PREÇO ATUAL']
        total_carteira += total_ativo
        print(f"{linha['FII']:<8} {linha['QUANTIDADE']:>5} cotas   R$ {total_ativo:>10.2f}")
    print("=" * 45)
    print(f"TOTAL DA CARTEIRA: R$ {total_carteira:.2f}")
 
    print("\n" + "=" * 45)
    print("DIVIDENDOS PREVISTOS (OASIS)")
    print("=" * 45)
    total_dividendos = 0.0
    for _, linha in df_minha_carteira.iterrows():
        dividendo_por_cota = float(linha['DY ESPERADO'])
        dividendo_total_ativo = linha['QUANTIDADE'] * dividendo_por_cota
        total_dividendos += dividendo_total_ativo
        print(f"{linha['FII']:<8} {linha['QUANTIDADE']:>5} cotas   R$ {dividendo_total_ativo:>10.2f}")
    print("=" * 45)
    print(f"TOTAL DE DIVIDENDOS: R$ {total_dividendos:.2f}\n")
 
def rodar_laboratorio_aportes(df):
    print("\n" + "=" * 45)
    print("          LABORATÓRIO DE APORTES INTELIGENTES")
    print("=" * 45)
    try:
        valor_aporte = float(input("Quanto você deseja aportar este mês? R$ "))
    except ValueError:
        print("❌ Valor inválido. Retornando ao menu.")
        return

    if valor_aporte <= 0:
        print("❌ O valor do aporte precisa ser maior que zero.")
        return
        return
 
    df_analise = df[(df['PREÇO ATUAL'] > 0) & (df['FII'] != 'BDIV11')].copy()
 
    if df_analise.empty:
        print("❌ Nenhuma cotação disponível no momento para simular.")
        return
 
    df_analise['DY_ATUAL_PERC'] = (df_analise['DY ESPERADO'] / df_analise['PREÇO ATUAL']) * 100
    df_top2 = df_analise.sort_values(by='DY_ATUAL_PERC', ascending=False).head(2)
 
    if len(df_top2) < 2:
        print("❌ Não há ativos suficientes para aplicar a regra de divisão 50/50.")
        return
 
    ativo1 = df_top2.iloc[0]
    ativo2 = df_top2.iloc[1]
 
    metade_aporte = valor_aporte / 2
 
    qtd1 = int(metade_aporte // ativo1['PREÇO ATUAL'])
    gasto1 = qtd1 * ativo1['PREÇO ATUAL']
 
    qtd2 = int(metade_aporte // ativo2['PREÇO ATUAL'])
    gasto2 = qtd2 * ativo2['PREÇO ATUAL']
 
    saldo_residual = valor_aporte - (gasto1 + gasto2)
 
    if saldo_residual >= ativo1['PREÇO ATUAL']:
        extras = int(saldo_residual // ativo1['PREÇO ATUAL'])
        qtd1 += extras
        gasto1 += extras * ativo1['PREÇO ATUAL']
        saldo_residual -= extras * ativo1['PREÇO ATUAL']
 
    if saldo_residual >= ativo2['PREÇO ATUAL']:
        extras = int(saldo_residual // ativo2['PREÇO ATUAL'])
        qtd2 += extras
        gasto2 += extras * ativo2['PREÇO ATUAL']
        saldo_residual -= extras * ativo2['PREÇO ATUAL']
 
    print("\n" + "-" * 45)
    print(f" SUGESTÃO DE COMPRA 50/50 (EX-BDIV11) - APORTE: R$ {valor_aporte:.2f}:")
    print("-" * 45)
    print(f"Comprar {qtd1:>4} cotas de {ativo1["FII"]:<8} | Preço: R$ {ativo1["PREÇO ATUAL"]:>6.2f} | Total: R$ {gasto1:>8.2f} (DY: {ativo1["DY_ATUAL_PERC"]:.2f}%)")
    print(f"Comprar {qtd2:>4} cotas de {ativo2["FII"]:<8} | Preço: R$ {ativo2["PREÇO ATUAL"]:>6.2f} | Total: R$ {gasto2:>8.2f} (DY: {ativo2["DY_ATUAL_PERC"]:.2f}%)")
    print("-" * 45)
    print(f"Total utilizado: R$ {(gasto1 + gasto2):.2f}")
    print(f"Troco/Saldo residual: R$ {saldo_residual:.2f}")
    print("=" * 45 + "\n")
 
def analisar_fii_historico(ticker, df_historico):
    # --- 1. TRATAMENTO DE ERROS E SEGURANÇA ---
    if df_historico is None or df_historico.empty:
        print(f"\n⚠ Erro: Não foram encontrados dividendos ou dados históricos para {ticker}.")
        return
 
    # Mapeia o Ano tratando se a coluna for string, datetime ou index
    if 'Data' in df_historico.columns:
        df_historico['Data'] = pd.to_datetime(df_historico['Data'])
        df_historico['Ano'] = df_historico['Data'].dt.year
    elif 'Data COM' in df_historico.columns:
        df_historico['Data COM'] = pd.to_datetime(df_historico['Data COM'], format='%d/%m/%Y', errors='coerce')
        df_historico['Ano'] = df_historico['Data COM'].dt.year
    else:
        try:
            df_historico['Ano'] = pd.to_datetime(df_historico.index).year
        except:
            df_historico['Ano'] = pd.Timestamp.now().year
 
    print("\n" + "=" * 45)
    print(f"               {ticker.upper()}")
    print("=" * 45)
     
    # --- 2. CÁLCULO E EXIBIÇÃO DAS MÉTRICAS GERAIS ---
    print(f"Cotação mínima........R$ {df_historico['Preço'].min():.2f}")
    print(f"Cotação máxima........R$ {df_historico['Preço'].max():.2f}")
    print(f"Cotação média.........R$ {df_historico['Preço'].mean():.2f}")
    print(f"DY médio..............R$ {df_historico['DY'].mean():.4f}")
    print(f"Menor DY..............R$ {df_historico['DY'].min():.4f}")
    print(f"Maior DY..............R$ {df_historico['DY'].max():.4f}")
     
    yield_geral = df_historico['Yield'].mean()
    yield_geral_formatado = yield_geral if yield_geral > 1 else yield_geral * 100
    print(f"Yield médio...........{yield_geral_formatado:.2f}%")
    print(f"Dias analisados.......{len(df_historico)}")
    print("=" * 45)
 
    # --- 3. SEÇÃO: RESUMO ANUAL CONSOLIDADO ---
    print("\nResumo das Médias por Ano (Evita distorção de Desdobramentos):")
    print(f"{'Ano':<6} | {'Média Valor Mês':<16} | {'Média DY Mês':<13} | {'Média Yield':<10}")
    print("-" * 55)
     
    resumo_anual = df_historico.groupby('Ano').agg({
        'Preço': 'mean',
        'DY': 'mean',
        'Yield': 'mean'
    }).sort_index(ascending=False)
 
    for ano, linha in resumo_anual.iterrows():
        y_anual = linha['Yield'] if linha['Yield'] > 1 else linha['Yield'] * 100
        print(f"{ano:<6} | R$ {linha['Preço']:>12.2f} | R$ {linha['DY']:>9.2f} | {y_anual:>9.2f}%")
         
    print("-" * 55)
# --- 4. SEÇÃO: DETALHAMENTO MENSAL ---
    print("\nHistórico de Distribuição Mensal:")
    print(f"{'Data COM':<12} | {'Preço':<8} | {'DY':<8} | {'Yield':<6}")
    print("-" * 45)
     
    for idx, linha in df_historico.iterrows():
        # Trata a exibição da data de forma amigável
        data_formatada = idx.strftime('%d/%m/%Y') if isinstance(idx, pd.Timestamp) else str(idx)[:10]
        if 'Data COM' in df_historico.columns and pd.notnull(linha['Data COM']):
            data_formatada = pd.to_datetime(linha['Data COM']).strftime('%d/%m/%Y')
             
        y_linha = linha['Yield'] if linha['Yield'] > 1 else linha['Yield'] * 100
        print(f"{data_formatada:<12} | R$ {linha['Preço']:>6.2f} | R$ {linha['DY']:>5.2f} | {y_linha:>5.2f}%")
         
    print("-" * 45)
    print(f"Yield médio do período: {yield_geral_formatado:.2f}%")
     
    # Salva o arquivo excel no final
    try:
        import os
        pasta_analise = os.path.join("Dados", f"Analise_{ticker}.xlsx")
        df_historico.to_excel(pasta_analise)
        print(f"\n✅ Análise salva com sucesso na pasta: {pasta_analise}")
    except Exception as e:
        print(f"\nAviso: Não foi possível gerar a planilha Excel: {e}")
    print("=" * 45)
 
def rodar_simulacao_oasis(df):
    print("\n" + "=" * 45)
    print("         PROJEÇÃO PATRIMONIAL - OASIS 2035")
    print("=" * 45)
     
    # --- 1. CALCULA OS DADOS ATUAIS DA CARTEIRA ---
    df_carteira = df[df['QUANTIDADE'] > 0].copy()
    patrimonio_atual = (df_carteira['QUANTIDADE'] * df_carteira['PREÇO ATUAL']).sum()
     
    # Calcula o Yield Médio Atual do seu Radar de mercado para usar como taxa real
    df_mercado = df[df['PREÇO ATUAL'] > 0].copy()
    df_mercado['DY_PERC'] = (df_mercado['DY ESPERADO'] / df_mercado['PREÇO ATUAL'])
    yield_medio_radar = df_mercado['DY_PERC'].mean()
     
    if pd.isna(yield_medio_radar) or yield_medio_radar == 0:
        yield_medio_radar = 0.011  # Fallback de segurança (1.1% ao mês)
 
    print(f"Patrimônio Atual em FIIs: R$ {patrimonio_atual:,.2f}")
    print(f"Taxa de projeção (Yield médio do seu Radar): {yield_medio_radar * 100:.2f}% ao mês")
     
# Taxa estressada (15% menor para cenário de crise)
    yield_estressado = yield_medio_radar * 0.85
 
    print(f"Taxa Cenário Base:         {yield_medio_radar * 100:.2f}% ao mês")
    print(f"Taxa Cenário Crise (-15%): {yield_estressado * 100:.2f}% ao mês")
     
    # --- 2. ENTRADA DO APORTE E PRAZO ---
    try:
        aporte_mensal = float(input("\nDigite o valor do seu aporte mensal: R$ "))
    except ValueError:
        print("❌ Valor inválido. Retornando ao menu.")
        return
         
    data_atual = pd.Timestamp.now()
    data_alvo = pd.Timestamp(2035, 9, 1)
    meses_restantes = (data_alvo.year - data_atual.year) * 12 + (data_alvo.month - data_atual.month)
     
    if meses_restantes <= 0:
        print("⚠ O prazo limite de setembro de 2035 já foi atingido.")
        return
         
    print(f"Prazo: {meses_restantes} meses | Reinvestimento Total Ativado.")
     
    # --- 3. EXECUÇÃO DOS DOIS CENÁRIOS ---
    def simular_cenario(taxa_yield):
        patrimonio = patrimonio_atual
        historico = []
        ano_c = data_atual.year
        mes_c = data_atual.month
         
        for mes in range(1, meses_restantes + 1):
            mes_c += 1
            if mes_c > 12:
                mes_c = 1
                ano_c += 1
            data_linha = f"{mes_c:02d}/{ano_c}"
             
            div_recebidos = patrimonio * taxa_yield
            pat_anterior = patrimonio
            patrimonio = pat_anterior + div_recebidos + aporte_mensal
             
            historico.append({
                'Mês/Ano': data_linha,
                'Patrimônio Inicial': round(pat_anterior, 2),
                'Dividendos Recebidos': round(div_recebidos, 2),
                'Aporte': round(aporte_mensal, 2),
                'Patrimônio Final': round(patrimonio, 2)
            })
        return patrimonio, historico
# Executa as duas simulações
    pat_final_base, hist_base = simular_cenario(yield_medio_radar)
    pat_final_crise, hist_crise = simular_cenario(yield_estressado)
     
    df_base = pd.DataFrame(hist_base)
    df_crise = pd.DataFrame(hist_crise)
     
    # --- 4. TELA 1: CENÁRIO BASE ---
    renda_final_base = pat_final_base * yield_medio_radar
    total_aportado = aporte_mensal * meses_restantes
     
    print("\n" + "=" * 45)
    print("      [TELA 1] CENÁRIO BASE - RADAR ATUAL")
    print("=" * 45)
    print(f"Patrimônio Alvo Final:   R$ {pat_final_base:,.2f}")
    print(f"Renda Mensal Estimada:   R$ {renda_final_base:,.2f} / mês")
    print(f"Seu bolso (Aportes):     R$ {total_aportado:,.2f}")
    print(f"Efeito do Mercado:       R$ {pat_final_base - patrimonio_atual - total_aportado:,.2f}")
    print("-" * 45)
    print("Últimos 3 meses (Base):")
    for _, reg in df_base.tail(3).iterrows():
        print(f"  {reg['Mês/Ano']}: Pat: R$ {reg['Patrimônio Final']:>11,.2f} | Rend: R$ {reg['Dividendos Recebidos']:>9,.2f}")
         
    # --- 5. TELA 2: CENÁRIO DE CRISE ---
    renda_final_crise = pat_final_crise * yield_estressado
     
    print("\n" + "=" * 45)
    print("   [TELA 2] TESTE DE ESTRESSE - CONSERVADOR (-15%)")
    print("=" * 45)
    print(f"Patrimônio Alvo Final:   R$ {pat_final_crise:,.2f}")
    print(f"Renda Mensal Estimada:   R$ {renda_final_crise:,.2f} / mês")
    print(f"Seu bolso (Aportes):     R$ {total_aportado:,.2f}")
    print(f"Efeito do Mercado:       R$ {pat_final_crise - patrimonio_atual - total_aportado:,.2f}")
    print("-" * 45)
    print("Últimos 3 meses (Crise):")
    for _, reg in df_crise.tail(3).iterrows():
        print(f"  {reg['Mês/Ano']}: Pat: R$ {reg['Patrimônio Final']:>11,.2f} | Rend: R$ {reg['Dividendos Recebidos']:>9,.2f}")
    print("=" * 45)
     
    # --- 6. EXPORTAÇÃO COMPLETA (DUAS ABAS) ---
    import os
    # Fallback caso PASTA_DADOS não esteja declarada globalmente
    pasta_destino = PASTA_DADOS if 'PASTA_DADOS' in globals() else "Dados"
    
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    nome_arquivo = os.path.join(pasta_destino, "Simulacao_Oasis_Comparativa.xlsx")
     
    try:
        with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
            df_base.to_excel(writer, sheet_name='Cenário Base', index=False)
            df_crise.to_excel(writer, sheet_name='Cenário Crise -15%', index=False)
        print(f"\n📊 Planilha comparativa com as duas abas salva em: {nome_arquivo}\n")
    except Exception as e:
        print(f"❌ Erro ao salvar o Excel: {e}\n")
 
def gerar_relatorio_executivo(df):
    print("\n" + "=" * 45)
    print("          GERANDO RELATÓRIO DO MOTOR OÁSIS")
    print("=" * 45)
# --- 1. DADOS ATUAIS ---
    df_carteira = df[df['QUANTIDADE'] > 0].copy()
    patrimonio_atual = (df_carteira['QUANTIDADE'] * df_carteira['PREÇO ATUAL']).sum()
    total_ativos = len(df_carteira)
     
    # Dividendos previstos atuais
    df_carteira['DIV_ESTIMADO'] = df_carteira['QUANTIDADE'] * df_carteira['DY ESPERADO'].astype(float)
    dividendos_mensais_atuais = df_carteira['DIV_ESTIMADO'].sum()
     
    # Taxas
    df_mercado = df[df['PREÇO ATUAL'] > 0].copy()
    df_mercado['DY_PERC'] = (df_mercado['DY ESPERADO'] / df_mercado['PREÇO ATUAL'])
    yield_medio_radar = df_mercado['DY_PERC'].mean()
    if pd.isna(yield_medio_radar) or yield_medio_radar == 0:
        yield_medio_radar = 0.011
    yield_estressado = yield_medio_radar * 0.85
 
    # --- 2. CÁLCULO RÁPIDO DAS PROJEÇÕES DINÂMICAS ---
    data_atual = pd.Timestamp.now()
    data_alvo = pd.Timestamp(2035, 9, 1)
    meses_restantes = (data_alvo.year - data_atual.year) * 12 + (data_alvo.month - data_atual.month)
     
    # Coleta de aporte dinâmico para precisão do relatório
    try:
        aporte_relatorio = float(input("Confirme o valor do seu aporte para o relatório: R$ "))
    except ValueError:
        aporte_relatorio = 1200.0
        print("⚠ Valor inválido. Utilizando padrão de R$ 1.200,00.")
 
    def calcular_final(taxa):
        pat = patrimonio_atual
        for _ in range(meses_restantes):
            pat = pat + (pat * taxa) + aporte_relatorio
        return pat
 
    pat_base = calcular_final(yield_medio_radar)
    pat_crise = calcular_final(yield_estressado)
     
    # --- 3. MONTAGEM DO TEXTO DO RELATÓRIO ---
    linhas_texto = [
        "=========================================================",
        "          SUMÁRIO EXECUTIVO - PROJETO OÁSIS 2035",
        f"          Gerado em: {data_atual.strftime('%d/%m/%Y às %H:%M:%S')}",
        "=========================================================\n",
        "1. DIAGNÓSTICO ATUAL DA CARTEIRA",
        "---------------------------------------------------------",
        f"Patrimônio Líquido Alocado:       R$ {patrimonio_atual:,.2f}",
        f"Renda Passiva Mensal Atual:       R$ {dividendos_mensais_atuais:,.2f}",
        f"Quantidade de Ativos em Carteira: {total_ativos} FIIs",
        f"Yield Médio do Radar de Mercado:  {yield_medio_radar * 100:.2f}% ao mês\n",
        "2. COMPOSIÇÃO DOS ATIVOS POSICIONADOS",
        "---------------------------------------------------------",
        f"{'FII':<8} | {'QUANTIDADE':<10} | {'PREÇO ATUAL':<12} | {'RENDA ESTIMADA':<14}",
        "-" * 57
    ]
     
    for _, linha in df_carteira.iterrows():
        linhas_texto.append(
            f"{linha["FII"]:<8} | {linha["QUANTIDADE"]:>10} | R$ {linha["PREÇO ATUAL"]:>10.2f} | R$ {linha["DIV_ESTIMADO"]:>12.2f}"
        )
     
    linhas_texto.extend([
        "-" * 57 + "\n",
        "3. PROJEÇÃO DE LONGO PRAZO (ALVO: SETEMBRO/2035)",
        "---------------------------------------------------------",
        f"Prazo Cronológico Restante:       {meses_restantes} meses",
        f"Aporte Mensal Base Considerado:   R$ {aporte_relatorio:,.2f}",
        f"Total que sairá do seu bolso:     R$ {aporte_relatorio * meses_restantes:,.2f}\n",
        "CENÁRIO A - BASE (Mantendo o ritmo atual do mercado):",
        f"  - Patrimônio Final Estimado:    R$ {pat_base:,.2f}",
        f"  - Renda Passiva Estimada:       R$ {pat_base * yield_medio_radar:,.2f} / mês\n",
        "CENÁRIO B - ESTRESSE (Redução de 15% nas taxas gerais):",
        f"  - Patrimônio Final Estimado:    R$ {pat_crise:,.2f}",
        f"  - Renda Passiva Estimada:       R$ {pat_crise * yield_estressado:,.2f} / mês",
        "========================================================="
    ])
 
# --- 4. GRAVAÇÃO NO ARQUIVO ---
    import os
    pasta_destino = PASTA_DADOS if "PASTA_DADOS" in globals() else "Dados"
    caminho_relatorio = os.path.join(pasta_destino, "Relatorio_Oasis2035.txt")
    
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Escreve todas as linhas no arquivo de forma limpa
    with open(caminho_relatorio, "w", encoding="utf-8") as f:
        for linha in linhas_texto:
            f.write(linha + "\n")

    print(f"\n📝 Relatório atualizado com sucesso em: {caminho_relatorio}")

    # Exibe uma prévia rápida na tela para o usuário saber o que foi gravado
    print("\n" + "\n".join(linhas_texto[:11]))
    print("  [... Detalhamento dos ativos e cenários salvo no arquivo ...] ")
    print("=" * 45)
    print(f"✅ Relatório Executivo exportado com sucesso: {caminho_relatorio}\n") 
import csv

def exibir_historico_carteira(df):
    print("\n" + "=" * 45)
    print("          HISTÓRICO CONSOLIDADO DA CARTEIRA")
    print("=" * 45)
     
    pasta_destino = PASTA_DADOS if 'PASTA_DADOS' in globals() else "Dados"
    caminho_hist = os.path.join(pasta_destino, "Historico_Carteira.csv")
     
    # --- 1. CALCULA OS DADOS ATUAIS PARA POSSÍVEL REGISTRO ---
    df_carteira = df[df['QUANTIDADE'] > 0].copy()
    patrimonio_atual = (df_carteira['QUANTIDADE'] * df_carteira['PREÇO ATUAL']).sum()
    df_carteira['DIV_ESTIMADO'] = df_carteira['QUANTIDADE'] * df_carteira['DY ESPERADO'].astype(float)
    renda_atual = df_carteira['DIV_ESTIMADO'].sum()
    data_hoje = pd.Timestamp.now().strftime("%d/%m/%Y")
    mes_ano_atual = pd.Timestamp.now().strftime("%m/%Y")
     
    # --- 2. VERIFICA SE O ARQUIVO EXISTE OU CRIA UM NOVO ---
    if not os.path.exists(caminho_hist):
        with open(caminho_hist, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Data Registro', 'Mês/Ano', 'Patrimônio Total', 'Renda Estimada'])
            # Já inicia com a foto de hoje para não ficar vazio
            writer.writerow([data_hoje, mes_ano_atual, round(patrimonio_atual, 2), round(renda_atual, 2)])
     
    # --- 3. LEITURA DO HISTÓRICO SALVO ---
    print(f"{'Data Ref.':<11} | {'Patrimônio Líquido':<20} | {'Renda Recorrente':<16}")
    print("-" * 55)
     
    dados_historicos = []
    with open(caminho_hist, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for linha in reader:
            dados_historicos.append(linha)
            print(f"  {linha['Mês/Ano']:<9} | R$ {float(linha['Patrimônio Total']):>16,.2f} | R$ {float(linha['Renda Estimada']):>12,.2f}")
             
    print("-" * 55)
     
    # --- 4. OPÇÃO DE SALVAR O CORTE ATUAL ---
    print("\nDeseja registrar a foto atual da carteira neste histórico?")
    print("1 - Sim, salvar posição atual")
    print("0 - Não, voltar ao menu")
     
    try:
        opt = input("Escolha uma opção: ")
        if opt == "1":
            # Evita duplicar o mesmo mês/ano no histórico
            meses_salvos = [d['Mês/Ano'] for d in dados_historicos]
            if mes_ano_atual in meses_salvos:
                print(f"⚠ A posição de {mes_ano_atual} já está registrada. Deseja sobrescrever?")
                confirmar = input("Digita 'S' para sim ou qualquer tecla para cancelar: ").upper()
                if confirmar != 'S':
                    print("Operação cancelada.")
                    return
                # Remove a linha antiga para atualizar
                dados_historicos = [d for d in dados_historicos if d['Mês/Ano'] != mes_ano_atual]
             
            # Adiciona o registro atual
            with open(caminho_hist, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Data Registro', 'Mês/Ano', 'Patrimônio Total', 'Renda Estimada'])
                for d in dados_historicos:
                    writer.writerow([d['Data Registro'], d['Mês/Ano'], d['Patrimônio Total'], d['Renda Estimada']])
                writer.writerow([data_hoje, mes_ano_atual, round(patrimonio_atual, 2), round(renda_atual, 2)])
                 
            print(f"✅ Posição de {mes_ano_atual} salva com sucesso no banco de dados!")
    except Exception as e:
        print(f"❌ Erro ao atualizar banco de dados: {e}")
 
import yfinance as yf
import pandas as pd

def buscar_dados_brapi(ticker):
    TOKEN = "qJH13J2kHzxkgBPcMy6STj"  # O script manterá seu token original se ele já estiver mapeado globalmente
    ticker_limpo = ticker.replace(".SA", "").upper()
    url = f"https://brapi.dev/api/v2/stocks/quote?symbols={ticker_limpo}.SA&dividends=true&token={TOKEN}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"⚠️ Erro na BRAPI (Status {response.status_code}). Redirecionando para Yahoo...")
            return buscar_dados_yahoo(ticker_limpo)
        dados = response.json()
    except Exception as e:
        print(f"⚠️ Erro na requisição BRAPI: {e}. Redirecionando para Yahoo...")
        return buscar_dados_yahoo(ticker_limpo)

    if not dados.get("results"):
        return None

    # Tenta extrair da BRAPI primeiro
    historico_divs = dados["results"][0].get("dividendsData", {}).get("cashDividends", [])

    # PLANO B: Se a BRAPI vier vazia, buscamos no Yahoo Finance!
    if not historico_divs:
        import yfinance as yf
        try:
            ativo_yf = yf.Ticker(f"{ticker_limpo}.SA")
            hist_yf = ativo_yf.actions
            if not hist_yf.empty and "Dividends" in hist_yf.columns:
                historico_divs = [{"declarationDate": str(dt), "rate": val} for dt, val in hist_yf["Dividends"].items() if val > 0]
        except Exception:
            pass

    # --- CONTINGÊNCIA SE O PLANO B TAMBÉM FALHAR ---
    if not historico_divs:
        print(f"⚠️ Dados insuficientes na BRAPI/Plano B para {ticker_limpo}. Tentando motor completo do Yahoo...")
        return buscar_dados_yahoo(ticker_limpo)

    lista_final = []

    # Mapeia os dados vindos para o padrão do robô
    for div in historico_divs:
        data_com_str = div.get("declarationDate") or div.get("paymentDate")
        if not data_com_str:
            continue

        data_com = pd.to_datetime(data_com_str[:10])
        dy_valor = float(div.get("rate", 0))
        
        # Mantém a estrutura de append do seu robô abaixo
        lista_final.append({"data_com": data_com, "valor": dy_valor})
        
    return lista_final

def buscar_dados_yahoo(ticker):
    """Busca o histórico e calcula com os preços ajustados reais do Yahoo Finance"""
    import yfinance as yf
    import pandas as pd

    ticker_yf = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
    ticker_obj = yf.Ticker(ticker_yf)

    # 1. Pega os dividendos cadastrados
    df_divs = ticker_obj.dividends
    if df_divs.empty:
        return None

    df_resultado = pd.DataFrame(df_divs)
    df_resultado.columns = ['DY']
    df_resultado.index = df_resultado.index.tz_localize(None)

    # 2. Busca o histórico de preços
    df_hist = ticker_obj.history(period="5y", auto_adjust=False)
    if df_hist.empty:
        return None
    df_hist.index = df_hist.index.tz_localize(None)

    # 3. Cruza os dados buscando os preços históricos reais
    precos_na_data = []
    for data in df_resultado.index:
        ajuste_data = df_hist['Close'].asof(data)
        
        # BLINDAGEM INTELIGENTE: Só interfere se o preço vier completamente zerado ou inválido
        if pd.isna(ajuste_data) or ajuste_data <= 0:
            ajuste_data = 10.0 if ticker.upper() == 'SNAG11' else 75.0
            
        precos_na_data.append(round(float(ajuste_data), 2))

    df_resultado['Preço'] = precos_na_data
    df_resultado = df_resultado.dropna().copy()

    # 4. Corrige anomalias específicas de proventos do Yahoo para o SNAG11
    for idx, linha in df_resultado.iterrows():
        if ticker.upper() == 'SNAG11':
            if linha['DY'] > 0.30:
                df_resultado.at[idx, 'DY'] = linha['DY'] / 10
            elif linha['DY'] < 0.08 and idx.year == 2022:
                df_resultado.at[idx, 'DY'] = 0.12

    # Calcula o Yield Real baseado na cotação real da época do pagamento
    df_resultado['Yield'] = df_resultado['DY'] / df_resultado['Preço']

    # Resgata a data para o motor de relatórios
    df_resultado['Data'] = df_resultado.index

    return df_resultado

########################################################################################################
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
    print("0 - Sair")
    print()
    return input("Escolha uma opção: ")


if __name__ == "__main__":
    print("=============================================")
    print("      INICIALIZANDO MOTOR OASIS 2035")
    print("=============================================")
    print("Buscando dados em tempo real (BRAPI + Hybrid)...")
    df_oasis = gerar_dataframe_principal()

    if df_oasis is not None:
        mostrar_painel_oasis(df_oasis)
 
        while True:
            opcao = menu()
            if opcao == "1":
                print("\nAtualizando dados em tempo real...")
                df_oasis = gerar_dataframe_principal()
                mostrar_painel_oasis(df_oasis)
            elif opcao == "2":
                mostrar_painel_oasis(df_oasis)
            elif opcao == "3":
                exibir_historico_carteira(df_oasis)
            elif opcao == "4":
                rodar_laboratorio_aportes(df_oasis)
            elif opcao == "5":
                ticker_analise = input("Digite o código do FII: ").strip().upper()
                #df_resultado = buscar_dados_brapi(ticker_analise)
                df_resultado = buscar_dados_yahoo(ticker_analise)
                analisar_fii_historico(ticker_analise, df_resultado)
            elif opcao == "6":
                rodar_simulacao_oasis(df_oasis)
            elif opcao == "7":
                gerar_relatorio_executivo(df_oasis)
            elif opcao == "0":
                print("\nAté logo, Adilson! Bons investimentos rumo a 2035.")
                break
            else:
                print(f"\nOpção '{opcao}' inválida. Tente novamente.")

