from Modulos.acoes import analisar_acoes_bazin, exibir_painel_bazin

# Lista de radar para testar o filtro de Bazin
radar_acoes = ["BBAS3", "ITSA4", "TAEE11", "SAPR11", "VALE3", "PETR4"]

df_bazin = analisar_acoes_bazin(radar_acoes)
exibir_painel_bazin(df_bazin)
