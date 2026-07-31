# -*- coding: utf-8 -*-
import os
import pandas as pd

def exportar_relatorio_executivo(df, data_atual, patrimonio_atual, yield_medio_radar, dividendos_mensais_atuais, total_ativos, df_carteira):
    """Executa os cálculos e exporta o Sumário Executivo do Projeto Oásis 2035"""
    
    data_alvo = pd.Timestamp(2035, 9, 1)
    meses_restantes = (data_alvo.year - data_atual.year) * 12 + (data_alvo.month - data_atual.month)
    
    if meses_restantes <= 0:
        print("⚠ O prazo limite de setembro de 2035 já foi atingido.")
        return

    # Coleta de aporte dinâmico
    try:
        aporte_relatorio = float(input("Confirme o valor do seu aporte para o relatório: R$ "))
    except ValueError:
        aporte_relatorio = 1200.0
        print("⚠ Valor inválido. Utilizando padrão de R$ 1.200,00.")

    yield_estressado = yield_medio_radar * 0.85

    # Função matemática de acúmulo com juros compostos
    def calcular_final(taxa):
        pat = patrimonio_atual
        for _ in range(meses_restantes):
            pat = pat + (pat * taxa) + aporte_relatorio
        return pat

    pat_base = calcular_final(yield_medio_radar)
    pat_crise = calcular_final(yield_estressado)
    
    # Função auxiliar para formatar no padrão brasileiro (R$ 43.821,16)
    def fmt_br(valor):
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # --- MONTAGEM DO TEXTO DO RELATÓRIO ---
    linhas_texto = [
        "=========================================================",
        "          SUMÁRIO EXECUTIVO - PROJETO OÁSIS 2035",
        "          Gerado em: " + data_atual.strftime('%d/%m/%Y às %H:%M:%S'),
        "=========================================================\n",
        "1. DIAGNÓSTICO ATUAL DA CARTEIRA",
        "---------------------------------------------------------",
        f"Patrimônio Líquido Alocado:       R$ {fmt_br(patrimonio_atual)}",
        f"Renda Passiva Mensal Atual:       R$ {fmt_br(dividendos_mensais_atuais)}",
        f"Quantidade de Ativos em Carteira: {total_ativos} FIIs",
        f"Yield Médio do Radar de Mercado:  {yield_medio_radar * 100:.2f}% ao mês\n",
        "2. COMPOSIÇÃO DOS ATIVOS POSICIONADOS",
        "---------------------------------------------------------",
        f"{'FII':<8} | {'QUANTIDADE':<10} | {'PREÇO ATUAL':<12} | {'RENDA ESTIMADA':<14}",
        "-" * 57
    ]
    
    for _, linha in df_carteira.iterrows():
        preco_f = fmt_br(linha['PREÇO ATUAL'])
        div_f = fmt_br(linha['DIV_ESTIMADO'])
        linhas_texto.append(
            f"{linha['FII']:<8} | {linha['QUANTIDADE']:>10} | R$ {preco_f:>10} | R$ {div_f:>12}"
        )
    
    linhas_texto.extend([
        "-" * 57 + "\n",
        "3. PROJEÇÃO DE LONGO PRAZO (ALVO: SETEMBRO/2035)",
        "---------------------------------------------------------",
        f"Prazo Cronológico Restante:       {meses_restantes} meses",
        f"Aporte Mensal Base Considerado:   R$ {fmt_br(aporte_relatorio)}",
        f"Total que sairá do seu bolso:     R$ {fmt_br(aporte_relatorio * meses_restantes)}\n",
        "CENÁRIO A - BASE (Mantendo o ritmo atual do mercado):",
        f"  - Patrimônio Final Estimado:     R$ {fmt_br(pat_base)}",
        f"  - Renda Passiva Estimada:        R$ {fmt_br(pat_base * yield_medio_radar)} / mês\n",
        "CENÁRIO B - ESTRESSE (Redução de 15% nas taxas gerais):",
        f"  - Patrimônio Final Estimado:     R$ {fmt_br(pat_crise)}",
        f"  - Renda Passiva Estimada:        R$ {fmt_br(pat_crise * yield_estressado)} / mês",
        "========================================================="
    ])
 
    # Gravando na pasta Dados
    pasta_destino = "Dados"
    caminho_relatorio = os.path.join(pasta_destino, "Relatorio_Oasis2035.txt")
    
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    with open(caminho_relatorio, "w", encoding="utf-8") as f:
        for linha in linhas_texto:
            f.write(linha + "\n")

    print(f"\n📝 Relatório atualizado com sucesso em: {caminho_relatorio}")

    # Prévia na tela para o Maestro
    print("\n" + "\n".join(linhas_texto[:11]))
    print("   [... Detalhamento dos ativos e cenários salvo no arquivo ...] ")
    print("=" * 45)
    print(f"✅ Relatório Executivo exportado com sucesso: {caminho_relatorio}\n")
