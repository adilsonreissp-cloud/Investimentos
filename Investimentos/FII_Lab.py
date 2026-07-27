import yfinance as yf
import pandas as pd

print("="*45)
print("          FII LAB")
print("="*45)
print()

fii = input("Digite o FII (Ex: VGIA11): ").upper()

anos = input("Quantos anos deseja analisar (1,3,5,10)? ")

if anos == "1":
    periodo = "1y"
elif anos == "3":
    periodo = "3y"
elif anos == "5":
    periodo = "5y"
elif anos == "10":
    periodo = "10y"
else:
    print("Período inválido.")
    exit()

ticker = fii + ".SA"

print()
print("Baixando histórico...")
print()

ativo = yf.Ticker(ticker)

dados = ativo.history(period=periodo)

if dados.empty:
    print("FII não encontrado.")
    exit()

dados = dados.reset_index()

dados["Data"] = dados["Date"].dt.strftime("%d/%m/%Y")

arquivo = fii + "_" + anos + "ANOS.csv"

dados = dados[[
    "Data",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume"
]]

dados.columns = [
    "Data",
    "Abertura",
    "Máxima",
    "Mínima",
    "Fechamento",
    "Volume"
]

dados.to_csv(
    arquivo,
    index=False,
    sep=";",
    decimal=","
)

print("="*45)
print(f"FII: {fii}")
print("="*45)
print()

print(f"Dias analisados : {len(dados)}")
print(f"Preço mínimo    : R$ {dados['Mínima'].min():.2f}")
print(f"Preço máximo    : R$ {dados['Máxima'].max():.2f}")
print(f"Preço médio     : R$ {dados['Fechamento'].mean():.2f}")
print(f"Preço atual     : R$ {dados['Fechamento'].iloc[-1]:.2f}")

print()
print("Arquivo salvo:")
print(arquivo)
