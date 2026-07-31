def calcular_nota(ativo):

    nota = 50

    if "PREÇO ATUAL" in ativo.index and ativo["PREÇO ATUAL"] > 0:
        nota += 10

    if "QUANTIDADE" in ativo.index and ativo["QUANTIDADE"] > 0:
        nota += 10

    if "SEGMENTO" in ativo.index:
        nota += 10

    if "GESTORA" in ativo.index:
        nota += 10

    if "CATEGORIA" in ativo.index:
        nota += 10

    return nota
