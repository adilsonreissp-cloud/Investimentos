import pandas as pd

def simular_aporte_oasis_5meses(valor_aporte_mensal, df_dados=None):
    """
    Plano de Rebalanceamento Oásis 2035:
    Divide o Aporte Mensal + Dividendos reinvestidos igualmente 
    APENAS nos 4 ativos menores (VGIA11, VGIR11, SNAG11, VHFA11), 
    ignorando compras de JMBI11 e BDIV11.
    """
    print("\n" + "=" * 65)
    print("      OÁSIS 2035 - PLANEJAMENTO DE APORTE MENSAL (DILUIÇÃO)")
    print("=" * 65)
    
    # Ativos alvo para diluir risco (JMBI11 e BDIV11 de fora)
    tickers_alvo = ['VGIA11', 'VGIR11', 'SNAG11', 'VHFA11']
    
    # Preços de referência
    precos_padrao = {'VGIA11': 8.50, 'VGIR11': 9.35, 'SNAG11': 9.74, 'VHFA11': 10.90}
    ativos_alvo = {}

    for t in tickers_alvo:
        preco = 0.0
        if df_dados is not None and not df_dados.empty:
            if 'FII' in df_dados.columns:
                match = df_dados[df_dados['FII'].astype(str).str.upper() == t]
                if not match.empty:
                    preco = float(match.iloc[0].get('PREÇO ATUAL', match.iloc[0].get('Preço', 0.0)))
        
        if preco <= 0:
            preco = precos_padrao.get(t, 10.0)
            
        ativos_alvo[t] = preco
    
    # Base de dividendos reinvestidos (pPode ajustar o valor fixo se mudar)
    dividendos_reinvestidos = 572.83
    total_disponivel = valor_aporte_mensal + dividendos_reinvestidos
    
    # Divisão cirúrgica igualitária (1/4 para cada um dos 4 fundos)
    valor_por_ativo = total_disponivel / len(ativos_alvo)
    
    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    print(f"Capital Mensal do Trabalho/Aporte: {fmt_br(valor_aporte_mensal)}")
    print(f"(+) Dividendos Reinvestidos:        {fmt_br(dividendos_reinvestidos)}")
    print(f"Total Disponível para Compras:     {fmt_br(total_disponivel)}")
    print("-" * 65)
    
    sobra_troco = 0.0
    for ticker, preco in ativos_alvo.items():
        cotas_a_comprar = int(valor_por_ativo // preco)
        valor_gasto = cotas_a_comprar * preco
        sobra_troco += (valor_por_ativo - valor_gasto)
        
        print(f"Comprar {cotas_a_comprar:>3} cotas de {ticker:<6} | Preço: R$ {preco:>5.2f} | Total: {fmt_br(valor_gasto):>12}")
    
    print("-" * 65)
    print(f"Sobra estimada de caixa (troco):    {fmt_br(sobra_troco)}")
    print("=" * 65 + "\n")

    # Registro no arquivo de histórico .txt
    try:
        with open("historico_aportes.txt", "a", encoding="utf-8") as f:
            data_str = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
            f.write(f"Data: {data_str} | Aporte: R$ {valor_aporte_mensal:.2f} | Reinvestido: R$ {total_disponivel:.2f}\n")
    except Exception:
        pass


def rodar_calculo_cenarios(patrimonio_atual, yield_medio_radar, aporte_mensal, meses_restantes, data_atual):
    """Executa a simulação separando o bloco fixo do BDIV11 dos demais ativos da carteira"""
    
    # Reduz um pouco o yield global para a média real dos demais ativos (excluindo a distorção)
    yield_dinamico_base = yield_medio_radar * 0.70  # Ajusta para refletir a média ponderada correta dos FIIs de papel/híbridos
    yield_estressado = yield_dinamico_base * 0.85
    
    # Premissas do Bloco Fixo: BDIV11 travado na pedra (310 cotas fixas)
    cotas_bdiv = 310
    provento_por_cota_bdiv = 0.11  # Valor unitário nominal do provento em R$
    patrimonio_bdiv_fixo = cotas_bdiv * 10.00  # Valor base alocado no BDIV para separar do bolo
    
    def simular_cenario(taxa_dinamica):
        patrimonio = patrimonio_atual
        historico = []

        for mes in range(1, meses_restantes + 1):
            mes_futuro = data_atual.month + mes - 1
            ano_futuro = data_atual.year + (mes_futuro - 1) // 12
            mes_futuro = (mes_futuro - 1) % 12 + 1
            data_linha = f"{mes_futuro:02d}/{ano_futuro}"

            pat_anterior = patrimonio
            
            # 1. Provento Fixo do BDIV11: Absolutamente constante em Reais todo mês
            div_bdiv = cotas_bdiv * provento_por_cota_bdiv
            
            # 2. Provento Dinâmico: Aplicado apenas sobre o patrimônio livre restante
            patrimonio_livre = max(0.0, pat_anterior - patrimonio_bdiv_fixo)
            div_dinamico = patrimonio_livre * taxa_dinamica
            
            # Total de dividendos do mês
            div_recebidos = div_bdiv + div_dinamico
            
            # 3. Patrimônio Final
            patrimonio = pat_anterior + div_recebidos + aporte_mensal

            historico.append({
                'Mês/Ano': data_linha,
                'Patrimônio Inicial': round(pat_anterior, 2),
                'Dividendos Recebidos': round(div_recebidos, 2),
                'Aporte': round(aporte_mensal, 2),
                'Patrimônio Final': round(patrimonio, 2)
            })
        return patrimonio, historico

    pat_base, hist_base = simular_cenario(yield_dinamico_base)
    pat_crise, hist_crise = simular_cenario(yield_estressado)
    
    return pat_base, hist_base, pat_crise, hist_crise
    print("=" * 45)
