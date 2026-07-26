import pandas as pd
import yfinance as yf

def analisar_acao_bazin_3anos(ticker, preco_teto_desejado_pct=0.06):
    """
    Calcula o Preço Teto Bazin usando a média móvel de dividendos de 3 anos (36M)
    e aplica travas de Payout (>100%) para evitar falsos positivos.
    """
    ticker_clean = str(ticker).strip().upper()
    ticker_sa = ticker_clean if ticker_clean.endswith(".SA") else f"{ticker_clean}.SA"

    resultado = {
        'ticker': ticker_clean,
        'preco_atual': None,
        'div_medio_3a': None,
        'preco_teto': None,
        'margem_seguranca': None,
        'payout': None,
        'status': '🔴 AGUARDAR'
    }

    try:
        ativo = yf.Ticker(ticker_sa)
        
        # Preço Atual
        hist = ativo.history(period="5d")
        if hist.empty:
            return resultado
        preco_atual = float(hist["Close"].iloc[-1])
        resultado['preco_atual'] = preco_atual

        # Dividendos Média 3 Anos
        divs = ativo.dividends
        if not divs.empty:
            hoje = pd.Timestamp.now(tz=divs.index.tz) if divs.index.tz else pd.Timestamp.now()
            inicio_36m = hoje - pd.DateOffset(years=3)
            divs_36m = divs[divs.index >= inicio_36m]

            if not divs_36m.empty:
                soma_3anos = float(divs_36m.sum())
                div_medio_anual = soma_3anos / 3.0
                resultado['div_medio_3a'] = div_medio_anual

                preco_teto = div_medio_anual / preco_teto_desejado_pct
                resultado['preco_teto'] = preco_teto

                if preco_atual > 0:
                    resultado['margem_seguranca'] = ((preco_teto - preco_atual) / preco_atual) * 100

        # Trava de Payout
        try:
            info = ativo.info
            payout = info.get('payoutRatio')
            if payout is not None:
                resultado['payout'] = float(payout)
        except Exception:
            pass

        # Regras de Status Anti-Miopia
        payout_val = resultado['payout']
        margem_val = resultado['margem_seguranca']

        if payout_val and payout_val > 1.0:
            resultado['status'] = "🟡 ANALISAR (Não Recorrente)"
        elif margem_val is not None and margem_val >= 20.0:
            resultado['status'] = "🟢 COMPRAR"
        elif margem_val is not None and margem_val > 0:
            resultado['status'] = "🟡 OBSERVAR"
        else:
            resultado['status'] = "🔴 AGUARDAR"

    except Exception:
        pass

    return resultado


def menu_radar_acoes(df_dados=None):
    """
    Função de entrada chamada pelo OASIS35.PY para exibir a análise das Ações.
    """
    print("\n" + "=" * 65)
    print("           RADAR DE AÇÕES - MÉTODO BAZIN 3 ANOS (OASIS 2035)")
    print("=" * 65)

    ticker = input("Digite o código da Ação (ex: VALE3, PETR4, ALOS3): ").strip().upper()
    if not ticker:
        return

    print(f"\n🔍 Analisando {ticker} com média móvel de 3 anos e filtro de Payout...")
    res = analisar_acao_bazin_3anos(ticker)

    if res['preco_atual'] is None:
        print(f"❌ Não foi possível obter dados para {ticker}.")
        return

    fmt_br = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if v else "N/D"
    fmt_pct = lambda v: f"{v:.2f}%".replace(".", ",") if v is not None else "N/D"

    print("\n" + "-" * 65)
    print(f" Ativo:               {res['ticker']}")
    print(f" Preço Atual:         {fmt_br(res['preco_atual'])}")
    print(f" Div. Médio (3 Anos): {fmt_br(res['div_medio_3a'])} / ano")
    print(f" Preço Teto Bazin:    {fmt_br(res['preco_teto'])}")
    print(f" Margem Segurança:    {fmt_pct(res['margem_seguranca'])}")
    print(f" Payout Estimado:     {fmt_pct(res['payout'] * 100 if res['payout'] else None)}")
    print(f" Status:              {res['status']}")
    print("-" * 65 + "\n")
