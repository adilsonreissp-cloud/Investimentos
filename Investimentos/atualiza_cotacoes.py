import unicodedata
from pathlib import Path
import pandas as pd
import requests

# 🔑 Token do Oásis 2035
TOKEN = "qJH13J2kHzxkgBPcMy6STj"


def normalizar(texto):
    """Remove acentos e deixa o texto padronizado em maiúsculas."""
    nfkd = unicodedata.normalize("NFD", str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).upper().strip()


PASTA = Path("/home/adilson/Investimentos")
NOME_ARQUIVO = (
    "financeiro ate a agosto 2035 sem trabalho CLT Cenario definido  sem fiptalvez.ods"
)
ARQUIVO = PASTA / NOME_ARQUIVO

if not ARQUIVO.exists():
    print(f"❌ Arquivo não encontrado: {ARQUIVO}")
    exit()

print("🔍 Lendo a aba COTAÇÕES...")

# Lê todas as abas da planilha para preservar a estrutura
excel_file = pd.ExcelFile(ARQUIVO, engine="odf")
todas_as_abas = {}

aba_cotacoes = None
for nome_aba in excel_file.sheet_names:
    if "COTAC" in normalizar(nome_aba):
        aba_cotacoes = nome_aba
    # Carrega cada aba mantendo como DataFrame
    todas_as_abas[nome_aba] = pd.read_excel(
        ARQUIVO, engine="odf", sheet_name=nome_aba, header=None
    )

if not aba_cotacoes:
    print("❌ Aba de Cotações não encontrada!")
    exit()

df_cotacoes = todas_as_abas[aba_cotacoes].astype(object)
atualizados = 0

# Percorre as células buscando tickers
for r in range(len(df_cotacoes)):
    for c in range(len(df_cotacoes.columns)):
        val = str(df_cotacoes.iloc[r, c]).strip().upper()

        if (
            len(val) in [6, 7]
            and val[:4].isalpha()
            and val[4:6].isdigit()
            and val != "JUL/26"
        ):
            ticker_limpo = val.replace(".SA", "").strip().upper()
            url = f"https://brapi.dev/api/v2/stocks/quote?symbols={ticker_limpo}.SA&token={TOKEN}"

            try:
                response = requests.get(url, timeout=10)
                preco = 0.0

                if response.status_code == 200:
                    dados = response.json()
                    if dados.get("results"):
                        res = dados["results"][0]
                        preco = res.get("regularMarketPrice") or res.get("data", {}).get("regularMarketPrice", 0.0)
                        preco = float(preco)

                if ticker_limpo == "SNAG11" and preco < 9.0:
                    preco = 10.10

                if preco > 0.0:
                    df_cotacoes.iat[r, c + 1] = round(preco, 2)
                    print(
                        f"✅ {ticker_limpo} -> R$ {preco:.2f} (Linha {r+1})"
                    )
                    atualizados += 1
            except Exception as e:
                print(f"❌ Erro ao buscar cotação de {ticker_limpo}: {e}")

# Atualiza a aba modificada no dicionário
todas_as_abas[aba_cotacoes] = df_cotacoes

if atualizados > 0:
    # Reescreve o arquivo inteiro de uma vez só com todas as abas intactas
    with pd.ExcelWriter(ARQUIVO, engine="odf") as writer:
        for nome_aba, df_aba in todas_as_abas.items():
            df_aba.to_excel(writer, sheet_name=nome_aba, index=False, header=False)

    print(
        f"\n🎉 NASCEU! {atualizados} cotações atualizadas e gravadas na planilha!"
    )
    print(
        "💡 Vá no LibreOffice Calc e clique em 'Arquivo > Recarregar' para ver o milagre!"
    )
else:
    print("\n⚠️ Nenhuma cotação foi atualizada.")
