# TermiSignal

Terminálová šifrovaná komunikační aplikace inspirovaná Signalem.

## Funkce

- Terminálový vzhled (černé pozadí, barevné texty)
- End-to-end šifrování
- Jednoduchá registrace a přihlášení
- Formát konverzace: `uživatel@něco: --- text ---`

## Instalace

### Z .deb balíčku

```bash
sudo dpkg -i termisignal.deb
sudo apt-get install -f  # Pro instalaci závislostí
```

### Z kódu

```bash
# Klonování repozitáře
git clone https://github.com/username/termisignal.git
cd termisignal

# Instalace závislostí
pip install -r requirements.txt

# Spuštění aplikace
python -m termisignal
```

## Použití

```bash
termisignal
```

## Licence

MIT
