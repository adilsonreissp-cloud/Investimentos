import pandas as pd
from Modulos.simulador import simular_investimento


def simular_aporte_oasis_5meses(valor_aporte_mensal, df_dados=None):
    """
    Simula a distribuição do aporte mensal + dividendos reinvestidos
    focando em equilibrar os ativos menores (exclui gigantes como JMBI11 e BDIV11).
    """
    print("\n" + "=" * 60)
    print("      OÁSIS 2035 - PLANEJAMENTO DE APORTE MENSAL")
    print("=" * 60)
    
    # 1. Ativos alvo de equilíbrio (exclui gigantes)
    tickers_alvo = ['VGIA11', 'VGIR11', 'SNAG11', 'VHFA11']
    
    # Preços com fallback inteligente
    precos_padrao = {'VGIA11': 8.50, 'VGIR11': 9.35, 'SNAG11': 9.74, 'VHFA11': 10.90}
    ativos_alvo = {}

    for t in tickers_alvo:
        preco = 0.0
        # Tenta buscar no df local se disponível
        if df_dados is not None and not df_dados.empty:
            match = df_dados[df_dados['FII'].astype(str).str.upper() == t] if 'FII' in df_dados.columns else pd.DataFrame()
            if not match.empty:
                preco = float(match.iloc[0].get('PREÇO ATUAL', match.iloc[0].get('Preço', 0.0)))
        
        # Se não achou no df ou ta zerado, pega o padrão conhecido
        if preco <= 0:
            preco = precos_padrao.get(t, 10.0)
            
        ativos_alvo[t] = preco
    
    # 2. Total de dividendos gerados para reinvestimento
    dividendos_reinvestidos = 572.83
    total_disponivel = valor_aporte_mensal + dividendos_reinvestidos
    
    # 3. Divisão igualitária entre os 4 fundos
    valor_por_ativo = total_disponivel / len(ativos_alvo)
    
    print(f"Capital Mensal do Trabalho/Aporte: R$ {valor_aporte_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"(+) Dividendos Reinvestidos:        R$ {dividendos_reinvestidos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Total Disponível para Compras:     R$ {total_disponivel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print("-" * 60)
    
    sobra_troco = 0.0
    for ticker, preco in ativos_alvo.items():
        cotas_a_comprar = int(valor_por_ativo // preco)
        valor_gasto = cotas_a_comprar * preco
        sobra_troco += (valor_por_ativo - valor_gasto)
        
        print(f"Comprar {cotas_a_comprar:>3} cotas de {ticker:<6} (a R$ {preco:>5.2f}) -> Gasto: R$ {valor_gasto:>7.2f}".replace(".", ","))
    
    print("-" * 60)
    print(f"Sobra estimada de caixa (troco):    R$ {sobra_troco:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print("=" * 60)

    # Opcional: Registra o histórico de aportes em arquivo .txt
    try:
        with open("historico_aportes.txt", "a", encoding="utf-8") as f:
            data_str = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
            f.write(f"Data: {data_str} | Aporte: R$ {valor_aporte_mensal:.2f} | Total: R$ {total_disponivel:.2f}\n")
    except Exception:
        pass


def menu_simulacoes(df):

    while True:

        print()
        print("=" * 45)
        print("SIMULAÇÕES (OASIS 2035)")
        print("=" * 45)

        print("1 - Aporte único")
        print("2 - Aporte mensal (Planejamento Oásis)")
        print("3 - Reinvestimento")
        print("4 - Meta de renda")
        print("0 - Voltar")

        opcao = input("\nEscolha: ").strip()

        if opcao == "1":

            simular_investimento(df)

        elif opcao == "2":

            try:
                val_str = input("\nDigite o valor do Aporte Mensal do bolso (ex: 1000): ").strip()
                val_str = val_str.replace("R$", "").replace(".", "").replace(",", ".")
                valor_aporte = float(val_str)
                simular_aporte_oasis_5meses(valor_aporte, df)
            except ValueError:
                print("❌ Valor inválido. Digite um número correto (ex: 500 ou 1000).")

        elif opcao == "3":

            print()
            print("Em desenvolvimento...")

        elif opcao == "4":

            print()
            print("Em desenvolvimento...")

        elif opcao == "0":

            break

        else:

            print()
            print("Opção inválida.")
