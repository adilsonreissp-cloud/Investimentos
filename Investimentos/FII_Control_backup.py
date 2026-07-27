import yfinance as yf
import pandas as pd
carteira = pd.read_csv("carteira.csv", sep=";")
dividendos = pd.read_csv("dividendos.csv", sep=";")
fiis = [
    "BDIV11.SA",
    "JMBI11.SA",
    "VGIA11.SA",
    "VGIR11.SA",
    "SNAG11.SA",
    "VHFA11.SA",
    "KNRI11.SA"
]

dados = []

print("=" * 35)
print("        FII CONTROL")
print("=" * 35)
print()

for fii in fiis:
    ativo = yf.Ticker(fii)
    preco = ativo.history(period="1d")["Close"].iloc[-1]

    nome = fii.replace(".SA", "")

    print(f"{nome:<10} R$ {preco:.2f}")

    dados.append({
        "FII": nome,
        "Preço": round(preco, 2)
    })

df = pd.DataFrame(dados)
df = df.merge(carteira, on="FII")

df["Patrimonio"] = df["Preço"] * df["Quantidade"]
df.to_csv("cotacoes.csv", index=False, sep=";", decimal=",")
print()
print("=" * 45)
print("CARTEIRA")
print("=" * 45)
print()
print("=" * 45)
print("DIVIDENDOS PREVISTOS")
print("=" * 45)

total_dy = 0

for _, ativo in carteira.iterrows():

    fii = ativo["FII"]
    qtd = ativo["Quantidade"]

    info = dividendos[dividendos["FII"] == fii]

    if not info.empty:

        dy = info.iloc[0]["DY"]

        valor = qtd * dy

        total_dy += valor

        print(f"{fii:<8} {qtd:>4} cotas   "
              f"R$ {valor:>8.2f}")

print("=" * 45)
print(f"TOTAL DE DIVIDENDOS: R$ {total_dy:.2f}")
for _, linha in df.iterrows():
    print(f"{linha['FII']:<8} "
          f"{int(linha['Quantidade']):>5} cotas   "
          f"R$ {linha['Patrimonio']:>10.2f}")

print("=" * 45)
print(f"TOTAL DA CARTEIRA: R$ {df['Patrimonio'].sum():.2f}")
print()
print("Arquivo cotacoes.csv atualizado.")
