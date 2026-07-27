import pandas as pd


def calcular_carteira(df, carteira, dividendos):

    df = df.merge(carteira, on="FII")

    df["Patrimonio"] = df["Preço"] * df["Quantidade"]

    df["Valor Investido"] = (
        df["PrecoMedio"] * df["Quantidade"]
    )

    df["Lucro R$"] = (
        df["Patrimonio"] - df["Valor Investido"]
    )

    df["Lucro %"] = (
        df["Lucro R$"] /
        df["Valor Investido"]
    ) * 100

    df = df.merge(
        dividendos[["FII", "DY"]],
        on="FII"
    )

    df["Renda"] = (
        df["Quantidade"] * df["DY"]
    )

    return df
