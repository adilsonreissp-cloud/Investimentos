def simular_investimento(df):

    print()
    print("=" * 45)
    print("SIMULADOR DE INVESTIMENTOS")
    print("=" * 45)

    valor = float(input("Valor para investir: R$ "))

    fii = input("FII: ").upper()

    ativo = df[df["FII"] == fii]

    if ativo.empty:

        print()
        print("FII não encontrado.")
        return

    preco = ativo.iloc[0]["Preço"]

    dy = ativo.iloc[0]["DY"]

    cotas = int(valor // preco)

    sobra = valor - (cotas * preco)

    renda = cotas * dy

    print()
    print("=" * 45)

    print(f"FII.................. {fii}")
    print(f"Preço................ R$ {preco:.2f}")
    print(f"Cotas................ {cotas}")
    print(f"Sobra................ R$ {sobra:.2f}")
    print(f"Dividendo estimado... R$ {renda:.2f}")

    print("=" * 45)
