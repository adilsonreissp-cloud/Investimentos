import pandas as pd

def carregar_carteira():

    carteira = pd.read_csv(
        "Dados/carteira.csv",
        sep=";"
    )

    return carteira
def listar_fiis(carteira):

    fiis = []

    for fii in carteira["FII"]:

        fiis.append(f"{fii}.SA")

    return fiis

