import pandas as pd
import os

PASTA_DADOS = "Dados"


def carregar_regras():
    """
    Carrega as regras de funcionamento de cada FII.
    """

    arquivo = os.path.join(PASTA_DADOS, "ativos.csv")

    df = pd.read_csv(arquivo, sep=";")

    df.columns = df.columns.str.upper().str.strip()

    df["FII"] = df["FII"].str.upper().str.strip()

    return df.set_index("FII")


def obter_regra(fii, regras):

    fii = fii.upper().strip()

    if fii in regras.index:
        return regras.loc[fii]

    return None
