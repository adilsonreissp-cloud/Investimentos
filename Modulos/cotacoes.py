import requests
from bs4 import BeautifulSoup
import yfinance as yf


def buscar_vpa_statusinvest(ticker):
    """
    Resgata o Valor Patrimonial por Cota (VPA) no Status Invest 
    para Fiagros e FIIs.
    """
    ticker_clean = str(ticker).strip().upper().replace(".SA", "")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    rotas = [
        f"https://statusinvest.com.br/fiagros/{ticker_clean.lower()}",
        f"https://statusinvest.com.br/fundos-imobiliarios/{ticker_clean.lower()}"
    ]

    for url in rotas:
        try:
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Localiza a tag do Valor Patrimonial por Cota
                blocos = soup.find_all('div', class_='info')
                for bloco in blocos:
                    title = bloco.find('h3', class_='title')
                    if title and 'valor patrimonial p/ cota' in title.text.lower():
                        val_str = bloco.find('strong', class_='value').text
                        val_limpo = val_str.replace('.', '').replace(',', '.').strip()
                        return float(val_limpo)
        except Exception:
            continue

    return None


def obter_pvp_efetivo(ticker, preco_atual):
    """
    Retorna o P/VP direto. 
    Ignora consulta em planilha e tenta Yahoo Finance primeiro;
    se nulo/incompleto (Fiagros), faz o scraping direto no Status Invest.
    """
    if not preco_atual or preco_atual <= 0:
        return None

    ticker_clean = str(ticker).strip().upper().replace(".SA", "")
    ticker_sa = f"{ticker_clean}.SA"

    # 1ª Tentativa: Yahoo Finance
    try:
        ativo = yf.Ticker(ticker_sa)
        info = ativo.info

        pvp_yf = info.get('priceToBook')
        if pvp_yf and float(pvp_yf) > 0:
            return float(pvp_yf)

        vpa_yf = info.get('bookValue')
        if vpa_yf and float(vpa_yf) > 0:
            return preco_atual / float(vpa_yf)
    except Exception:
        pass

    # 2ª Tentativa (Contingência Instantânea): Scraping Status Invest
    vpa_web = buscar_vpa_statusinvest(ticker_clean)
    if vpa_web and vpa_web > 0:
        return preco_atual / vpa_web

    return None
