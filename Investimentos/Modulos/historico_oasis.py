# -*- coding: utf-8 -*-
import os
import csv
import pandas as pd

def processar_historico_carteira(df, pasta_dados="Dados"):
    print("\n" + "=" * 55)
    print("           HISTÓRICO CONSOLIDADO DA CARTEIRA")
    print("=" * 55)
     
    if not os.path.exists(pasta_dados):
        os.makedirs(pasta_dados)

    caminho_hist = os.path.join(pasta_dados, "Historico_Carteira.csv")
     
    # --- 1. CALCULA OS DADOS ATUAIS PARA POSSÍVEL REGISTRO ---
    df_carteira = df[df['QUANTIDADE'] > 0].copy()
    
    # Tratamento seguro dos tipos de dados
    df_carteira['QUANTIDADE'] = pd.to_numeric(df_carteira['QUANTIDADE'], errors='coerce').fillna(0)
    df_carteira['PREÇO ATUAL'] = pd.to_numeric(df_carteira['PREÇO ATUAL'], errors='coerce').fillna(0)
    df_carteira['DY ESPERADO'] = pd.to_numeric(df_carteira['DY ESPERADO'], errors='coerce').fillna(0)

    patrimonio_atual = (df_carteira['QUANTIDADE'] * df_carteira['PREÇO ATUAL']).sum()
    df_carteira['DIV_ESTIMADO'] = df_carteira['QUANTIDADE'] * df_carteira['DY ESPERADO']
    renda_atual = df_carteira['DIV_ESTIMADO'].sum()
    
    data_hoje = pd.Timestamp.now().strftime("%d/%m/%Y")
    mes_ano_atual = pd.Timestamp.now().strftime("%m/%Y")
     
    # --- 2. VERIFICA SE O ARQUIVO EXISTE OU CRIA O CABEÇALHO ---
    if not os.path.exists(caminho_hist):
        with open(caminho_hist, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Data Registro', 'Mês/Ano', 'Patrimônio Total', 'Renda Estimada'])
     
    # --- 3. LEITURA E EXIBIÇÃO DO HISTÓRICO SALVO ---
    dados_historicos = []
    with open(caminho_hist, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for linha in reader:
            dados_historicos.append(linha)

    print(f"{'Data Ref.':<10} | {'Patrimônio Líquido':<20} | {'Renda Recorrente':<16}")
    print("-" * 55)

    if not dados_historicos:
        print("⚠ Nenhum histórico registrado até o momento.")
    else:
        for linha in dados_historicos:
            val_patr = float(linha['Patrimônio Total']) if linha['Patrimônio Total'] else 0.0
            val_renda = float(linha['Renda Estimada']) if linha['Renda Estimada'] else 0.0
            
            patr_br = f"{val_patr:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            renda_br = f"{val_renda:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            print(f"  {linha['Mês/Ano']:<8} | R$ {patr_br:>16} | R$ {renda_br:>12}")
             
    print("-" * 55)
     
    # --- 4. OPÇÃO DE SALVAR O CORTE ATUAL ---
    print("\nDeseja registrar a foto atual da carteira neste histórico?")
    print("1 - Sim, salvar posição atual")
    print("0 - Não, voltar ao menu")
     
    try:
        opt = input("Escolha uma opção: ").strip()
        if opt == "1":
            # Evita duplicar o mesmo mês/ano no histórico
            meses_salvos = [d['Mês/Ano'] for d in dados_historicos]
            if mes_ano_atual in meses_salvos:
                print(f"\n⚠ A posição de {mes_ano_atual} já está registrada. Deseja sobrescrever?")
                confirmar = input("Digite 'S' para sim ou qualquer outra tecla para cancelar: ").strip().upper()
                if confirmar != 'S':
                    print("Operação cancelada.")
                    return
                # Remove a linha antiga para atualizar
                dados_historicos = [d for d in dados_historicos if d['Mês/Ano'] != mes_ano_atual]
             
            # Adiciona o novo registro e regrava o histórico completo
            with open(caminho_hist, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Data Registro', 'Mês/Ano', 'Patrimônio Total', 'Renda Estimada'])
                for d in dados_historicos:
                    writer.writerow([d['Data Registro'], d['Mês/Ano'], d['Patrimônio Total'], d['Renda Estimada']])
                writer.writerow([data_hoje, mes_ano_atual, round(patrimonio_atual, 2), round(renda_atual, 2)])
                 
            print(f"\n✅ Posição de {mes_ano_atual} salva com sucesso no banco de dados!")
    except Exception as e:
        print(f"\n❌ Erro ao atualizar banco de dados: {e}")
