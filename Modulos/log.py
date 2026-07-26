from datetime import datetime


def registrar(texto):

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    with open("Dados/OASIS.log", "a", encoding="utf-8") as arquivo:

        arquivo.write(f"[{agora}] {texto}\n")

