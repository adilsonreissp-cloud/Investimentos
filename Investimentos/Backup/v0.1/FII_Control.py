import yfinance as yf
import pandas as pd

# =====================================================
# LEITURA DOS ARQUIVOS
# =====================================================

carteira = pd.read_csv("carteira.csv", sep=";")
dividendos = pd.read_csv("dividendos.csv", sep=";")

# =====================================================
# LISTA DOS FIIs
# =====================================================

fiis = [
    "BDIV11.SA",
    "JMBI11.SA",
    "VGIA11.SA",
    "VGIR11.SA",
    "SNAG11.SA",
    "VHFA11.SA",
    "KNRI11.SA"
]

# =====================================================
# BUSCA DAS COTAÇÕES
# =====================================================

dados = []

print("=" * 35)
print("        FII CONTROL")
print("=" * 35)
print()

for fii in fiis:

    ativo = yf.Ticker(fii)
    preco = ativo.history(period="1d")["Close"].iloc[-1]

    nome = fii.replace(".SA", "")

    print(f"{nome:<8} R$ {preco:.2f}")

    dados.append({
        "FII": nome,
        "Preço": round(preco, 2)
    })

# =====================================================
# CARTEIRA
# =====================================================

df = pd.DataFrame(dados)

df = df.merge(carteira, on="FII")

df["Patrimonio"] = df["Preço"] * df["Quantidade"]
# Valor investido pelo preço médio
df["Valor Investido"] = df["PrecoMedio"] * df["Quantidade"]

# Lucro / Prejuízo em reais
df["Lucro R$"] = df["Patrimonio"] - df["Valor Investido"]

# Lucro / Prejuízo em %
df["Lucro %"] = (df["Lucro R$"] / df["Valor Investido"]) * 100

# Junta o DY da tabela de dividendos
df = df.merge(dividendos[["FII", "DY"]], on="FII")

# Calcula renda prevista
df["Renda"] = df["Quantidade"] * df["DY"]
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
print(f"TOTAL DA CARTEIRA: R$ {df['Patrimonio'].sum():.2f}")

# =====================================================
# DIVIDENDOS
# =====================================================

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

        print(f"{fii:<8}{qtd:>5} cotas   R$ {valor:>8.2f}")

print("=" * 45)
print(f"TOTAL DE DIVIDENDOS: R$ {total_dy:.2f}")

# =====================================================
# EXPORTAÇÃO
# =====================================================

# Organiza as colunas do relatório
df = df[
    [
        "FII",
        "Preço",
        "PrecoMedio",
        "Quantidade",
        "Valor Investido",
        "Patrimonio",
        "Lucro R$",
        "Lucro %",
        "DY",
        "Renda"
    ]
]

# Grava o relatório
df["Preço"] = df["Preço"].round(2)
df["PrecoMedio"] = df["PrecoMedio"].round(2)

df["Valor Investido"] = df["Valor Investido"].round(2)
df["Patrimonio"] = df["Patrimonio"].round(2)

df["Lucro R$"] = df["Lucro R$"].round(2)
df["Lucro %"] = df["Lucro %"].round(2)

df["DY"] = df["DY"].round(2)
df["Renda"] = df["Renda"].round(2)
df.to_csv(
    "cotacoes.csv",
    index=False,
    sep=";",
    decimal=","
)

print()
print("Arquivo cotacoes.csv atualizado.")
print()
print("✔ Relatório salvo em cotacoes.csv")
