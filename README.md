# LakyLukPerun 2.0

Automatický obchodní systém pro kryptoměny využívající technické indikátory z TradingView.

## Funkce

- Obchodování s kryptoměnami na Alpaca
- Analýza technických indikátorů z TradingView
- Podpora více kryptoměn (BTC, ETH, XRP, SOL, DOGE, XMR)
- Simulační režim pro testování bez reálných obchodů
- Detailní logování obchodů a signálů
- Možnost instalace na Synology NAS

## Instalace

### Z .deb balíčku

```bash
sudo dpkg -i lakylinuperun.deb
sudo apt-get install -f  # Pro instalaci závislostí
```

### Z kódu

```bash
# Klonování repozitáře
git clone https://github.com/sjeror11/lakylukperun.git
cd lakylukperun

# Instalace závislostí
pip install -r requirements.txt

# Spuštění aplikace
python perun_taapi_simple.py
```

### Na Synology NAS

Viz soubor `navod_instalace_perun_synology.md` pro podrobný návod.

## Použití

```bash
# Spuštění hlavního obchodního systému
python perun_taapi_simple.py

# Spuštění simulačního režimu
python run_simulation.py
```

## Konfigurace

Upravte soubor `.env` pro nastavení API klíčů a dalších parametrů:

```
ALPACA_API_KEY=váš_api_klíč
ALPACA_SECRET_KEY=váš_tajný_klíč
```

## Licence

MIT
