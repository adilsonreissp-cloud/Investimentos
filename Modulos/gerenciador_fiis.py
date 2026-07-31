import os
import pandas as pd
import os
import pandas as pd

PASTA_DADOS = "Dados"
ARQUIVO_CARTEIRA = os.path.join(PASTA_DADOS, "carteira.csv")
ARQUIVO_ATIVOS = os.path.join(PASTA_DADOS, "ativos.csv")

def carregar_carteira():
    """Lê o arquivo Dados/carteira.csv com tratamento de colunas e separador"""
    if os.path.exists(ARQUIVO_CARTEIRA):
        try:
            df = pd.read_csv(ARQUIVO_CARTEIRA, sep=";")
            # Normaliza os nomes das colunas
            df.columns = df.columns.str.strip()
            # Ajusta variações de nome de coluna
            if "Qtde" in df.columns:
                df = df.rename(columns={"Qtde": "Quantidade"})
            if "QUANTIDADE" in df.columns:
                df = df.rename(columns={"QUANTIDADE": "Quantidade"})
            if "PREÇO MÉDIO" in df.columns:
                df = df.rename(columns={"PREÇO MÉDIO": "PrecoMedio"})
            if "PRECO MEDIO" in df.columns:
                df = df.rename(columns={"PRECO MEDIO": "PrecoMedio"})
            return df
        except Exception as e:
            print(f"⚠️ Erro ao ler carteira: {e}")
    return pd.DataFrame(columns=["FII", "Quantidade", "PrecoMedio"])

def salvar_carteira(df):
    """Salva o DataFrame de volta no Dados/carteira.csv"""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    df.to_csv(ARQUIVO_CARTEIRA, sep=";", index=False)

def garantir_cadastro_ativo(ticker, preco_medio=10.0, dy_esperado=0.10):
    """Garante que o FII também exista no Dados/ativos.csv para não dar erro no merge"""
    if os.path.exists(ARQUIVO_ATIVOS):
        try:
            df_a = pd.read_csv(ARQUIVO_ATIVOS, sep=";")
            df_a.columns = df_a.columns.str.strip()
            if ticker not in df_a["FII"].values:
                nova_linha = pd.DataFrame([{
                    "FII": ticker,
                    "CATEGORIA": "Outros",
                    "SEGMENTO": "Outros",
                    "GESTORA": "Outras",
                    "DY ESPERADO": dy_esperado
                }])
                df_a = pd.concat([df_a, nova_linha], ignore_index=True)
                df_a.to_csv(ARQUIVO_ATIVOS, sep=";", index=False)
        except Exception as e:
            print(f"⚠️ Alerta ao atualizar ativos.csv: {e}")

def listar_carteira(df):
    """Exibe a lista atual de FIIs na tela."""
    print("\nFIIs na carteira atual:")
    for i, row in df.iterrows():
        qtd = int(row['Quantidade'])
        lbl_cota = "cota" if qtd == 1 else "cotas"
        print(f"{i + 1} - {row['FII']} ({qtd} {lbl_cota})")

def selecionar_fii(df):
    """Auxiliar para escolher um FII por índice ou Ticker."""
    if df.empty:
        print("❌ Sua carteira de FIIs está vazia.")
        return None, None
        
    listar_carteira(df)
    escolha = input("\nDigite o número ou código do FII (ou Enter para cancelar): ").strip().upper()
    
    if not escolha:
        return None, None
        
    if escolha.isdigit():
        idx = int(escolha) - 1
        if 0 <= idx < len(df):
            return idx, df.at[idx, "FII"]
    else:
        if escolha in df["FII"].values:
            idx = df[df["FII"] == escolha].index[0]
            return idx, escolha

    print("❌ FII não encontrado.")
    return None, None

# -------------------------------------------------------------
# 1. GERENCIAR ATIVOS (INCLUSÃO E EXCLUSÃO TOTAL)
# -------------------------------------------------------------

def incluir_novo_fii():
    """Adiciona um novo ticker à carteira."""
    df = carregar_carteira()
    print("\n--- ➕ INCLUIR NOVO FII NA CARTEIRA ---")
    ticker = input("Digite o código do novo FII (ex: HGLG11): ").strip().upper().replace(".SA", "")
    
    if not ticker:
        print("🟡 Operação cancelada.")
        return
        
    if ticker in df["FII"].values:
        print(f"⚠️ O FII {ticker} já existe na sua carteira! Use a opção de 'Gerenciar Cotas' para alterar o saldo.")
        return
        
    try:
        qtd = int(input(f"Quantas cotas de {ticker} você possui inicialmente? "))
        if qtd <= 0:
            print("❌ A quantidade inicial deve ser maior que zero.")
            return
        pm = float(input("Preço médio de compra (R$): ").replace(',', '.'))
    except ValueError:
        print("❌ Valor inválido digitado.")
        return
        
    novo_registro = pd.DataFrame([{"FII": ticker, "Quantidade": qtd, "PrecoMedio": pm}])
    df = pd.concat([df, novo_registro], ignore_index=True)
    salvar_carteira(df)
    garantir_cadastro_ativo(ticker, pm)
    
    lbl_cota = "cota" if qtd == 1 else "cotas"
    print(f"✅ FII {ticker} cadastrado com sucesso com {qtd} {lbl_cota}!")

def excluir_fii_completo():
    """Remove um FII por completo da carteira."""
    df = carregar_carteira()
    print("\n--- 🗑️ EXCLUIR FII DA CARTEIRA ---")
    idx, ticker = selecionar_fii(df)
    
    if idx is None:
        return
        
    confirma = input(f"⚠️ Tem certeza que deseja REMOVER O FII {ticker} COMPLETO da carteira? (S/N): ").strip().upper()
    if confirma == "S":
        df = df.drop(idx).reset_index(drop=True)
        salvar_carteira(df)
        print(f"🗑️ FII {ticker} removido completamente da carteira!")
    else:
        print("🟡 Operação cancelada.")

def sub_menu_gerenciar_ativos():
    """Submenu de nível Ativo."""
    while True:
        print("\n" + "-" * 40)
        print("      1. GERENCIAR ATIVOS (FIIs)")
        print("-" * 40)
        print("1 - Incluir Novo FII")
        print("2 - Excluir FII Completo")
        print("0 - Voltar")
        print("-" * 40)
        
        op = input("Escolha uma opção: ").strip()
        if op == "1":
            incluir_novo_fii()
        elif op == "2":
            excluir_fii_completo()
        elif op == "0":
            break
        else:
            print("Opção inválida.")

# -------------------------------------------------------------
# 2. GERENCIAR COTAS (APORTES E VENDAS PARCIAIS)
# -------------------------------------------------------------

def adicionar_cotas():
    """Soma cotas a um FII existente."""
    df = carregar_carteira()
    print("\n--- ➕ ADICIONAR COTAS (APORTE) ---")
    idx, ticker = selecionar_fii(df)
    
    if idx is None:
        return
        
    try:
        qtd_add = int(input(f"Quantas cotas deseja ADICIONAR ao FII {ticker}? "))
        if qtd_add <= 0:
            print("❌ Quantidade inválida.")
            return
    except ValueError:
        print("❌ Digite um número inteiro.")
        return
        
    df.at[idx, "Quantidade"] = int(df.at[idx, "Quantidade"]) + qtd_add
    salvar_carteira(df)
    nova_qtd = int(df.at[idx, "Quantidade"])
    lbl_cota = "cota" if nova_qtd == 1 else "cotas"
    print(f"✅ Adicionadas {qtd_add} cotas! Novo saldo de {ticker}: {nova_qtd} {lbl_cota}.")

def remover_cotas():
    """Subtrai cotas de um FII existente."""
    df = carregar_carteira()
    print("\n--- ➖ REMOVER COTAS (VENDA PARCIAL) ---")
    idx, ticker = selecionar_fii(df)
    
    if idx is None:
        return
        
    qtd_atual = int(df.at[idx, "Quantidade"])
    try:
        qtd_sub = int(input(f"Saldo atual: {qtd_atual}. Quantas cotas deseja SUBTRAIR? "))
        if qtd_sub <= 0:
            print("❌ Quantidade inválida.")
            return
    except ValueError:
        print("❌ Digite um número inteiro.")
        return

    if qtd_sub >= qtd_atual:
        confirma = input(f"⚠️ A quantidade ({qtd_sub}) é igual ou maior que o saldo ({qtd_atual}). Deseja REMOVER O FII {ticker} da carteira? (S/N): ").strip().upper()
        if confirma == "S":
            df = df.drop(idx).reset_index(drop=True)
            salvar_carteira(df)
            print(f"🗑️ Saldo zerado e FII {ticker} removido da carteira!")
        else:
            print("🟡 Operação cancelada.")
    else:
        df.at[idx, "Quantidade"] = qtd_atual - qtd_sub
        salvar_carteira(df)
        restantes = int(df.at[idx, "Quantidade"])
        lbl_cota = "cota" if restantes == 1 else "cotas"
        print(f"✅ Subtraídas {qtd_sub} cotas. Saldo atualizado de {ticker}: {restantes} {lbl_cota}.")

def sub_menu_gerenciar_cotas():
    """Submenu de nível Cotas."""
    while True:
        print("\n" + "-" * 40)
        print("      2. GERENCIAR COTAS")
        print("-" * 40)
        print("1 - Adicionar Cotas (Aporte)")
        print("2 - Subtrair Cotas (Venda Parcial)")
        print("0 - Voltar")
        print("-" * 40)
        
        op = input("Escolha uma opção: ").strip()
        if op == "1":
            adicionar_cotas()
        elif op == "2":
            remover_cotas()
        elif op == "0":
            break
        else:
            print("Opção inválida.")

# -------------------------------------------------------------
# MENU PRINCIPAL DO MÓDULO FII
# -------------------------------------------------------------

def menu_gerenciar_fiis():
    """Menu Conceitual Principal para Carteira FII"""
    while True:
        print("\n" + "=" * 45)
        print(" " * 10 + "GERENCIAR CARTEIRA FII")
        print("=" * 45)
        print("1 - Gerenciar Ativos (Adicionar / Remover FII)")
        print("2 - Gerenciar Cotas (Comprar / Vender Cotas)")
        print("0 - Voltar ao Menu Principal")
        print("=" * 45)
        
        op = input("Escolha uma opção: ").strip()
        if op == "1":
            sub_menu_gerenciar_ativos()
        elif op == "2":
            sub_menu_gerenciar_cotas()
        elif op == "0":
            break
        else:
            print("Opção inválida.")
