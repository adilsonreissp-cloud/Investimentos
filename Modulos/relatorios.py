import pandas as pd


def mostrar_carteira(df):

    print()
    print("=" * 45)
    print("CARTEIRA")
    print("=" * 45)

    for _, linha in df.iterrows():

        print(
            f"{linha['FII']:<8}"
            f"{int(linha['Quantidade']):>5} cotas   "
            f"R$ {linha['Patrimonio']:>10.2f}"
        )

    print("=" * 45)
    print(
        f"TOTAL DA CARTEIRA: "
        f"R$ {df['Patrimonio'].sum():.2f}"
    )


def mostrar_dividendos(df):

    print()
    print("=" * 45)
    print("DIVIDENDOS PREVISTOS")
    print("=" * 45)

    total = 0

    for _, linha in df.iterrows():

        total += linha["Renda"]

        print(
            f"{linha['FII']:<8}"
            f"{int(linha['Quantidade']):>5} cotas   "
            f"R$ {linha['Renda']:>8.2f}"
        )

    print("=" * 45)
    print(
        f"TOTAL DE DIVIDENDOS: "
        f"R$ {total:.2f}"
    )


def salvar_relatorio(df, pasta_dados):

    relatorio = df.copy()

    relatorio["Preço"] = relatorio["Preço"].round(2)
    relatorio["PrecoMedio"] = relatorio["PrecoMedio"].round(2)

    relatorio["Valor Investido"] = relatorio["Valor Investido"].round(2)
    relatorio["Patrimonio"] = relatorio["Patrimonio"].round(2)

    relatorio["Lucro R$"] = relatorio["Lucro R$"].round(2)
    relatorio["Lucro %"] = relatorio["Lucro %"].round(2)

    relatorio["DY"] = relatorio["DY"].round(2)
    relatorio["Renda"] = relatorio["Renda"].round(2)

    relatorio.to_csv(
        f"{pasta_dados}/cotacoes.csv",
        index=False,
        sep=";",
        decimal=","
    )

    print()
    print("Arquivo cotacoes.csv atualizado.")
    print()
    print("✔ Relatório salvo em cotacoes.csv")
