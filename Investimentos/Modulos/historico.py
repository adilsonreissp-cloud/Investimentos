import yfinance as yf
import os


def baixar_historico(fii, anos=10):
    ticker = fii + ".SA"

    print()
    print("=" * 45)
    print("BAIXANDO HISTÓRICO")
    print("=" * 45)

    ativo = yf.Ticker(ticker)
    dados = ativo.history(period=f"{anos}y")

    if dados.empty:
        print("Não foi possível baixar o histórico.")
        return

    pasta = "Historico"
    os.makedirs(pasta, exist_ok=True)

    arquivo = os.path.join(pasta, f"{fii}.csv")

    dados.to_csv(arquivo, sep=";", decimal=",")

    print()
    print("Histórico salvo em:")
    print(arquivo)
    print(f"Registros: {len(dados)}")
    ticker = fii + ".SA"

    print()
    print("=" * 45)
    print("BAIXANDO HISTÓRICO")
    print("=" * 45)

    ativo = yf.Ticker(ticker)

    dados = ativo.history(period=f"{anos}y")

    if dados.empty:
        print("Não foi possível baixar o histórico.")
        return

    pasta = "Historico"

    os.makedirs(pasta, exist_ok=True)

    arquivo = os.path.join(pasta, f"{fii}.csv")

    dados.to_csv(arquivo, sep=";", decimal=",")

import pandas as pd

def consultar_data(fii, data):

    arquivo = f"Historico/{fii}.csv"

    try:

        df = pd.read_csv(
            arquivo,
            sep=";",
            decimal=","
        )

    except:

        print("Histórico não encontrado.")
        return

    df["Date"] = df["Date"].str[:10]

    linha = df[df["Date"] == data]

    if linha.empty:

        print("Data não encontrada.")

    else:

        preco = linha.iloc[0]["Close"]

        print()
        print("="*40)
        print(f"{fii}")
        print(data)
        print(f"Fechamento: R$ {preco:.2f}")
    print()
