import yfinance as yf
import pandas as pd
from Modulos.simulador import simular_investimento
from Modulos.simulacoes import menu_simulacoes
from Modulos.comparador import comparar_fiis
from Modulos.calculos import calcular_carteira
from Modulos.relatorios import mostrar_carteira
from Modulos.relatorios import mostrar_dividendos
from Modulos.relatorios import salvar_relatorio
from Modulos.carteira import ( carregar_carteira, listar_fiis)
from Modulos.cotacoes import atualizar_cotacoes
PASTA_DADOS = "Dados"
Dividendos = pd.read_csv(f"{PASTA_DADOS}/dividendos.csv", sep=";")
def menu():

    print()
    print("=" * 45)
    print("          FII CONTROL")
    print("=" * 45)

    print("1 - Atualizar cotações")
    print("2 - Mostrar carteira")
    print("3 - Histórico")
    print("4 - Laboratório")
    print("5 - Comparar FIIs")
    print("6 - Simulações")
    print("7 - Relatórios")
    print("0 - Sair")
    print()

    opcao = input("Escolha uma opção: ")

    return opcao
# =====================================================
# LEITURA DOS ARQUIVOS
#=====================================================
carteira = carregar_carteira()
dividendos = pd.read_csv(f"{PASTA_DADOS}/dividendos.csv", sep=";")
fiis = listar_fiis(carteira)

# =====================================================
# LISTA DOS FIIs
# =====================================================

# =====================================================
# BUSCA DAS COTAÇÕES
# =====================================================

print("=" * 35)
print("        FII CONTROL")
print("=" * 35)
print()

df = atualizar_cotacoes(fiis)

for _, linha in df.iterrows():

    print(f"{linha['FII']:<8} R$ {linha['Preço']:.2f}")


# =====================================================
# CARTEIRA
# ===================================================

df = calcular_carteira(
    df,
    carteira,
    dividendos
)
mostrar_carteira(df)

# =====================================================
# DIVIDENDOS
# =====================================================

mostrar_dividendos(df)

# =====================================================
# EXPORTAÇÃO
# =====================================================

# Organiza as colunas do relatório
salvar_relatorio(df, PASTA_DADOS)
opcao = menu()

if opcao == "5":

    comparar_fiis(df)

elif opcao == "6":

    menu_simulacoes(df)

elif opcao == "0":

    print()
    print("Até logo!")

else:

    print()
    print(f"Você escolheu a opção {opcao}")
