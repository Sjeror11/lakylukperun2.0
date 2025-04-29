#!/bin/bash
# Skript pro řešení problémů s terminálem pro Midnight Commander

echo "=== Řešení problémů s terminálem pro Midnight Commander ==="
echo ""

# Kontrola aktuálního nastavení terminálu
echo "Aktuální nastavení terminálu:"
echo "TERM=$TERM"
echo "COLORTERM=$COLORTERM"
echo ""

# Kontrola dostupných terminfo
echo "Kontroluji dostupné terminfo..."
TERMINFO_DIRS=(
    "/usr/share/terminfo"
    "/usr/local/share/terminfo"
    "/opt/share/terminfo"
    "/lib/terminfo"
)

for dir in "${TERMINFO_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Nalezen adresář terminfo: $dir"
        echo "Dostupné typy terminálů:"
        find "$dir" -type f -name "x*" | sort | head -10
        echo "..."
    fi
done

echo ""

# Vytvoření adresáře terminfo
echo "Vytvářím adresář terminfo..."
mkdir -p ~/.terminfo/x

# Stažení definice xterm-256color
echo "Stahuji definici xterm-256color..."
if command -v curl &> /dev/null; then
    curl -s https://raw.githubusercontent.com/alacritty/alacritty/master/extra/terminfo/alacritty.terminfo > ~/.terminfo/alacritty.terminfo
    curl -s https://raw.githubusercontent.com/tmux/tmux/master/xterm-256color.terminfo > ~/.terminfo/xterm-256color.terminfo
elif command -v wget &> /dev/null; then
    wget -q -O ~/.terminfo/alacritty.terminfo https://raw.githubusercontent.com/alacritty/alacritty/master/extra/terminfo/alacritty.terminfo
    wget -q -O ~/.terminfo/xterm-256color.terminfo https://raw.githubusercontent.com/tmux/tmux/master/xterm-256color.terminfo
else
    echo "Nelze stáhnout definice terminfo. Chybí curl nebo wget."
fi

# Kompilace terminfo
echo "Kompiluji terminfo..."
if command -v tic &> /dev/null; then
    tic -x ~/.terminfo/alacritty.terminfo
    tic -x ~/.terminfo/xterm-256color.terminfo
else
    echo "Nelze kompilovat terminfo. Chybí příkaz tic."
fi

# Vytvoření skriptu pro spouštění mc s různými nastaveními terminálu
echo "Vytvářím skripty pro spouštění mc s různými nastaveními terminálu..."

# Hledání instalace mc
MC_PATHS=(
    "/usr/bin/mc"
    "/usr/local/bin/mc"
    "/opt/bin/mc"
    "/volume1/@appstore/mc/bin/mc"
    "/var/packages/mc/target/bin/mc"
    "$HOME/mc_install/bin/mc"
)

MC_PATH=""
for path in "${MC_PATHS[@]}"; do
    if [ -f "$path" ] && [ -x "$path" ]; then
        MC_PATH="$path"
        echo "Nalezen Midnight Commander: $MC_PATH"
        break
    fi
done

if [ -z "$MC_PATH" ]; then
    echo "Midnight Commander nebyl nalezen."
    echo "Zkuste ho nejprve nainstalovat pomocí jednoho z instalačních skriptů."
    exit 1
fi

# Vytvoření skriptů pro různé typy terminálů
TERM_TYPES=("xterm" "xterm-256color" "screen" "screen-256color" "linux" "vt100")

for term_type in "${TERM_TYPES[@]}"; do
    cat > ~/mc_${term_type}.sh << EOF
#!/bin/bash
export TERM=$term_type
export TERMINFO=~/.terminfo
$MC_PATH -d "\$@"
EOF
    
    chmod +x ~/mc_${term_type}.sh
    echo "Vytvořen skript: ~/mc_${term_type}.sh"
done

# Vytvoření skriptu pro spuštění mc bez barev
cat > ~/mc_nocolor.sh << EOF
#!/bin/bash
$MC_PATH -d -c "\$@"
EOF

chmod +x ~/mc_nocolor.sh
echo "Vytvořen skript: ~/mc_nocolor.sh"

echo ""
echo "=== Řešení problémů dokončeno ==="
echo "Vytvořil jsem několik skriptů pro spuštění Midnight Commander s různými nastaveními terminálu."
echo "Zkuste postupně tyto skripty, dokud nenajdete ten, který funguje:"
for term_type in "${TERM_TYPES[@]}"; do
    echo "- ~/mc_${term_type}.sh"
done
echo "- ~/mc_nocolor.sh (bez barev)"
echo ""
echo "Pokud žádný z těchto skriptů nefunguje, zkuste nainstalovat balíček ncurses-terminfo:"
echo "sudo /opt/bin/opkg install ncurses-terminfo"
