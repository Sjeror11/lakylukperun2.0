# Návod na instalaci Midnight Commander na Synology NAS

Tento návod vám pomůže nainstalovat a zprovoznit Midnight Commander (mc) na vašem Synology NAS.

## Předpoklady

- Přístup k Synology NAS přes SSH
- Oprávnění sudo nebo root
- Povolený SSH přístup v DSM (Control Panel > Terminal & SNMP > Enable SSH service)

## Metoda 1: Instalace přes SynoCommunity

1. Přidejte repozitář SynoCommunity do vašeho Synology NAS:
   - Otevřete DSM (Diskstation Manager)
   - Jděte do Package Center > Settings > Package Sources
   - Klikněte na Add a zadejte:
     - Name: SynoCommunity
     - Location: https://packages.synocommunity.com/
   - Klikněte na OK

2. Nainstalujte Midnight Commander:
   - V Package Center klikněte na Community
   - Vyhledejte "Midnight Commander"
   - Klikněte na Install

## Metoda 2: Instalace přes Entware

Pokud metoda 1 nefunguje, můžete zkusit instalaci přes Entware:

1. Nainstalujte Entware:
   ```bash
   sudo wget -O - https://raw.githubusercontent.com/Entware/Entware/master/installer/generic.sh | /bin/sh
   ```

2. Přidejte Entware do PATH:
   ```bash
   echo 'export PATH=$PATH:/opt/bin:/opt/sbin' >> ~/.bashrc
   source ~/.bashrc
   ```

3. Nainstalujte Midnight Commander:
   ```bash
   sudo /opt/bin/opkg update
   sudo /opt/bin/opkg install mc
   ```

## Metoda 3: Použití připravených skriptů

1. Nahrajte skripty na váš Synology NAS:
   ```bash
   scp install_mc_synology.sh diagnose_mc_synology.sh sjeror@192.168.1.139:~
   ```

2. Připojte se přes SSH a spusťte diagnostický skript:
   ```bash
   ssh sjeror@192.168.1.139
   chmod +x diagnose_mc_synology.sh
   ./diagnose_mc_synology.sh
   ```

3. Na základě výsledků diagnostiky spusťte instalační skript:
   ```bash
   chmod +x install_mc_synology.sh
   sudo ./install_mc_synology.sh
   ```

## Řešení problémů

### Problém: mc není v PATH

Pokud je mc nainstalován, ale není v PATH, přidejte cestu do PATH:
```bash
echo 'export PATH=$PATH:/cesta/k/adresari/s/mc' >> ~/.bashrc
source ~/.bashrc
```

### Problém: Chybějící závislosti

Pokud mc hlásí chybějící knihovny, nainstalujte je:
```bash
sudo /opt/bin/opkg install ncurses-terminfo ncurses
```

### Problém: Problémy s terminálem

Pokud mc nefunguje správně kvůli nastavení terminálu, použijte:
```bash
TERM=xterm-256color mc -d
```

### Problém: Oprávnění

Pokud nemáte dostatečná oprávnění:
```bash
sudo chmod +x /cesta/k/mc
```

## Alternativní řešení

Pokud se vám nepodaří zprovoznit mc, můžete použít jiné správce souborů:

1. **Webové rozhraní DSM** - pro základní správu souborů
2. **File Station** - nativní aplikace Synology pro správu souborů
3. **SSH + základní příkazy** - ls, cd, cp, mv, rm, atd.

## Kontakt pro pomoc

Pokud budete potřebovat další pomoc, můžete:
1. Zkontrolovat logy: `cat /var/log/messages | grep mc`
2. Spustit diagnostický skript a poslat výsledky
3. Vyzkoušet alternativní metody instalace
