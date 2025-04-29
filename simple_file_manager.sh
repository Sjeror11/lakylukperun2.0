#!/bin/bash
# Jednoduchý souborový manažer v Bash pro Synology NAS
# Alternativa k Midnight Commander

VERSION="1.0"
CURRENT_DIR=$(pwd)
HISTORY=()
HISTORY_POS=0
SELECTED_ITEM=0
ITEMS_PER_PAGE=15
CURRENT_PAGE=0

# Barvy
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
BOLD='\033[1m'
RESET='\033[0m'

# Funkce pro vyčištění obrazovky
clear_screen() {
    clear
}

# Funkce pro zobrazení hlavičky
show_header() {
    echo -e "${BOLD}${BLUE}=== Jednoduchý souborový manažer v${RED} Bash ${BLUE}===${RESET}"
    echo -e "${YELLOW}Verze: ${VERSION}${RESET}"
    echo -e "${GREEN}Aktuální adresář: ${CYAN}$CURRENT_DIR${RESET}"
    echo -e "${MAGENTA}Strana: $((CURRENT_PAGE+1))${RESET}"
    echo ""
}

# Funkce pro zobrazení nápovědy
show_help() {
    echo -e "${BOLD}${YELLOW}Nápověda:${RESET}"
    echo -e "${CYAN}q${RESET} - Ukončit"
    echo -e "${CYAN}h${RESET} - Zobrazit nápovědu"
    echo -e "${CYAN}j${RESET} - Posunout dolů"
    echo -e "${CYAN}k${RESET} - Posunout nahoru"
    echo -e "${CYAN}l${RESET} nebo ${CYAN}Enter${RESET} - Otevřít adresář/soubor"
    echo -e "${CYAN}h${RESET} nebo ${CYAN}Backspace${RESET} - Přejít do nadřazeného adresáře"
    echo -e "${CYAN}c${RESET} - Kopírovat soubor/adresář"
    echo -e "${CYAN}m${RESET} - Přesunout soubor/adresář"
    echo -e "${CYAN}r${RESET} - Přejmenovat soubor/adresář"
    echo -e "${CYAN}d${RESET} - Smazat soubor/adresář"
    echo -e "${CYAN}n${RESET} - Vytvořit nový adresář"
    echo -e "${CYAN}t${RESET} - Vytvořit nový soubor"
    echo -e "${CYAN}s${RESET} - Zobrazit velikost adresáře/souboru"
    echo -e "${CYAN}p${RESET} - Zobrazit oprávnění"
    echo -e "${CYAN}f${RESET} - Hledat soubor/adresář"
    echo -e "${CYAN}z${RESET} - Komprimovat soubor/adresář"
    echo -e "${CYAN}x${RESET} - Extrahovat archiv"
    echo -e "${CYAN}b${RESET} - Přejít zpět v historii"
    echo -e "${CYAN}w${RESET} - Přejít vpřed v historii"
    echo -e "${CYAN}g${RESET} - Přejít na začátek seznamu"
    echo -e "${CYAN}G${RESET} - Přejít na konec seznamu"
    echo -e "${CYAN}PgUp${RESET} - Předchozí strana"
    echo -e "${CYAN}PgDn${RESET} - Další strana"
    echo -e "${CYAN}Home${RESET} - Přejít do domovského adresáře"
    echo -e "${CYAN}e${RESET} - Upravit soubor (pomocí nano/vi)"
    echo -e "${CYAN}v${RESET} - Zobrazit soubor (pomocí less/cat)"
    echo ""
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro získání seznamu souborů a adresářů
get_items() {
    local items=()
    
    # Přidat speciální položku pro nadřazený adresář
    items+=("..")
    
    # Získat seznam adresářů a souborů
    local dirs=($(ls -p | grep / | sort))
    local files=($(ls -p | grep -v / | sort))
    
    # Přidat adresáře a soubory do seznamu
    for dir in "${dirs[@]}"; do
        items+=("$dir")
    done
    
    for file in "${files[@]}"; do
        items+=("$file")
    done
    
    echo "${items[@]}"
}

# Funkce pro zobrazení seznamu souborů a adresářů
show_items() {
    local items=($@)
    local total_items=${#items[@]}
    local start_idx=$((CURRENT_PAGE * ITEMS_PER_PAGE))
    local end_idx=$((start_idx + ITEMS_PER_PAGE - 1))
    
    if [ $end_idx -ge $total_items ]; then
        end_idx=$((total_items - 1))
    fi
    
    for i in $(seq $start_idx $end_idx); do
        local item="${items[$i]}"
        if [ $i -eq $SELECTED_ITEM ]; then
            if [[ "$item" == */ ]]; then
                echo -e "${BOLD}${GREEN}> $item${RESET}"
            else
                echo -e "${BOLD}${WHITE}> $item${RESET}"
            fi
        else
            if [[ "$item" == */ ]]; then
                echo -e "${GREEN}  $item${RESET}"
            else
                echo -e "  $item"
            fi
        fi
    done
    
    # Doplnit prázdné řádky, aby seznam měl vždy stejnou výšku
    local remaining=$((ITEMS_PER_PAGE - (end_idx - start_idx + 1)))
    for i in $(seq 1 $remaining); do
        echo ""
    done
}

# Funkce pro přidání adresáře do historie
add_to_history() {
    # Odstranit vše za aktuální pozicí v historii
    HISTORY=("${HISTORY[@]:0:$((HISTORY_POS+1))}")
    
    # Přidat nový adresář do historie
    HISTORY+=("$1")
    HISTORY_POS=$((${#HISTORY[@]} - 1))
}

# Funkce pro přechod do adresáře
change_directory() {
    local target="$1"
    
    if [ "$target" = ".." ]; then
        cd ..
    else
        cd "$target"
    fi
    
    CURRENT_DIR=$(pwd)
    SELECTED_ITEM=0
    CURRENT_PAGE=0
    add_to_history "$CURRENT_DIR"
}

# Funkce pro otevření souboru
open_file() {
    local file="$1"
    
    # Zjistit typ souboru
    local file_type=$(file -b "$file")
    
    if [[ "$file_type" == *text* ]]; then
        # Textový soubor - zobrazit pomocí less
        less "$file"
    elif [[ "$file_type" == *image* ]]; then
        # Obrázek - informovat uživatele
        echo "Soubor je obrázek. Nelze zobrazit v terminálu."
        read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
    elif [[ "$file_type" == *executable* ]]; then
        # Spustitelný soubor - zeptat se, zda ho spustit
        read -p "Soubor je spustitelný. Chcete ho spustit? (a/n): " choice
        if [ "$choice" = "a" ]; then
            ./"$file"
            read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
        fi
    else
        # Ostatní soubory - zobrazit pomocí hexdump
        hexdump -C "$file" | less
    fi
}

# Funkce pro kopírování souboru/adresáře
copy_item() {
    local source="$1"
    read -p "Zadejte cílovou cestu: " target
    
    if [ -d "$source" ]; then
        cp -r "$source" "$target"
    else
        cp "$source" "$target"
    fi
    
    echo "Kopírování dokončeno."
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro přesun souboru/adresáře
move_item() {
    local source="$1"
    read -p "Zadejte cílovou cestu: " target
    
    mv "$source" "$target"
    
    echo "Přesun dokončen."
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro přejmenování souboru/adresáře
rename_item() {
    local source="$1"
    read -p "Zadejte nový název: " new_name
    
    mv "$source" "$new_name"
    
    echo "Přejmenování dokončeno."
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro smazání souboru/adresáře
delete_item() {
    local item="$1"
    read -p "Opravdu chcete smazat '$item'? (a/n): " choice
    
    if [ "$choice" = "a" ]; then
        if [ -d "$item" ]; then
            rm -r "$item"
        else
            rm "$item"
        fi
        echo "Smazání dokončeno."
    else
        echo "Smazání zrušeno."
    fi
    
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro vytvoření nového adresáře
create_directory() {
    read -p "Zadejte název nového adresáře: " dir_name
    
    mkdir "$dir_name"
    
    echo "Adresář vytvořen."
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro vytvoření nového souboru
create_file() {
    read -p "Zadejte název nového souboru: " file_name
    
    touch "$file_name"
    
    echo "Soubor vytvořen."
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro zobrazení velikosti souboru/adresáře
show_size() {
    local item="$1"
    
    if [ -d "$item" ]; then
        du -sh "$item"
    else
        ls -lh "$item" | awk '{print $5}'
    fi
    
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro zobrazení oprávnění
show_permissions() {
    local item="$1"
    
    ls -l "$item"
    
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro hledání souboru/adresáře
find_item() {
    read -p "Zadejte hledaný výraz: " search_term
    
    find . -name "*$search_term*" | less
    
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro komprimaci souboru/adresáře
compress_item() {
    local item="$1"
    read -p "Zadejte název archivu (bez přípony): " archive_name
    
    if [ -d "$item" ]; then
        tar -czvf "${archive_name}.tar.gz" "$item"
    else
        gzip -c "$item" > "${archive_name}.gz"
    fi
    
    echo "Komprimace dokončena."
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro extrakci archivu
extract_archive() {
    local archive="$1"
    
    if [[ "$archive" == *.tar.gz ]]; then
        tar -xzvf "$archive"
    elif [[ "$archive" == *.gz ]]; then
        gunzip "$archive"
    elif [[ "$archive" == *.zip ]]; then
        unzip "$archive"
    else
        echo "Nepodporovaný formát archivu."
    fi
    
    echo "Extrakce dokončena."
    read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
}

# Funkce pro úpravu souboru
edit_file() {
    local file="$1"
    
    if command -v nano &> /dev/null; then
        nano "$file"
    elif command -v vi &> /dev/null; then
        vi "$file"
    else
        echo "Nenalezen žádný textový editor."
        read -n 1 -s -r -p "Stiskněte libovolnou klávesu pro pokračování..."
    fi
}

# Hlavní smyčka
main() {
    # Inicializace historie
    HISTORY=("$CURRENT_DIR")
    
    while true; do
        clear_screen
        show_header
        
        # Získat seznam položek
        local items=($(get_items))
        
        # Zobrazit položky
        show_items "${items[@]}"
        
        # Zobrazit patičku
        echo ""
        echo -e "${YELLOW}Použijte ${CYAN}h${YELLOW} pro nápovědu, ${CYAN}q${YELLOW} pro ukončení${RESET}"
        
        # Čekat na vstup od uživatele
        read -n 1 -s key
        
        case "$key" in
            q)
                # Ukončit
                clear_screen
                exit 0
                ;;
            h)
                # Zobrazit nápovědu
                clear_screen
                show_help
                ;;
            j)
                # Posunout dolů
                if [ $SELECTED_ITEM -lt $((${#items[@]} - 1)) ]; then
                    SELECTED_ITEM=$((SELECTED_ITEM + 1))
                    
                    # Pokud je vybraná položka mimo aktuální stránku, přejít na další stránku
                    if [ $SELECTED_ITEM -gt $((CURRENT_PAGE * ITEMS_PER_PAGE + ITEMS_PER_PAGE - 1)) ]; then
                        CURRENT_PAGE=$((CURRENT_PAGE + 1))
                    fi
                fi
                ;;
            k)
                # Posunout nahoru
                if [ $SELECTED_ITEM -gt 0 ]; then
                    SELECTED_ITEM=$((SELECTED_ITEM - 1))
                    
                    # Pokud je vybraná položka mimo aktuální stránku, přejít na předchozí stránku
                    if [ $SELECTED_ITEM -lt $((CURRENT_PAGE * ITEMS_PER_PAGE)) ]; then
                        CURRENT_PAGE=$((CURRENT_PAGE - 1))
                    fi
                fi
                ;;
            l|"")
                # Otevřít adresář/soubor
                local selected="${items[$SELECTED_ITEM]}"
                
                if [ -d "$selected" ]; then
                    change_directory "$selected"
                else
                    open_file "$selected"
                fi
                ;;
            $'\177'|$'\b')
                # Backspace - přejít do nadřazeného adresáře
                change_directory ".."
                ;;
            c)
                # Kopírovat soubor/adresář
                local selected="${items[$SELECTED_ITEM]}"
                if [ "$selected" != ".." ]; then
                    copy_item "$selected"
                fi
                ;;
            m)
                # Přesunout soubor/adresář
                local selected="${items[$SELECTED_ITEM]}"
                if [ "$selected" != ".." ]; then
                    move_item "$selected"
                fi
                ;;
            r)
                # Přejmenovat soubor/adresář
                local selected="${items[$SELECTED_ITEM]}"
                if [ "$selected" != ".." ]; then
                    rename_item "$selected"
                fi
                ;;
            d)
                # Smazat soubor/adresář
                local selected="${items[$SELECTED_ITEM]}"
                if [ "$selected" != ".." ]; then
                    delete_item "$selected"
                fi
                ;;
            n)
                # Vytvořit nový adresář
                create_directory
                ;;
            t)
                # Vytvořit nový soubor
                create_file
                ;;
            s)
                # Zobrazit velikost adresáře/souboru
                local selected="${items[$SELECTED_ITEM]}"
                show_size "$selected"
                ;;
            p)
                # Zobrazit oprávnění
                local selected="${items[$SELECTED_ITEM]}"
                show_permissions "$selected"
                ;;
            f)
                # Hledat soubor/adresář
                find_item
                ;;
            z)
                # Komprimovat soubor/adresář
                local selected="${items[$SELECTED_ITEM]}"
                if [ "$selected" != ".." ]; then
                    compress_item "$selected"
                fi
                ;;
            x)
                # Extrahovat archiv
                local selected="${items[$SELECTED_ITEM]}"
                if [ "$selected" != ".." ]; then
                    extract_archive "$selected"
                fi
                ;;
            b)
                # Přejít zpět v historii
                if [ $HISTORY_POS -gt 0 ]; then
                    HISTORY_POS=$((HISTORY_POS - 1))
                    cd "${HISTORY[$HISTORY_POS]}"
                    CURRENT_DIR=$(pwd)
                    SELECTED_ITEM=0
                    CURRENT_PAGE=0
                fi
                ;;
            w)
                # Přejít vpřed v historii
                if [ $HISTORY_POS -lt $((${#HISTORY[@]} - 1)) ]; then
                    HISTORY_POS=$((HISTORY_POS + 1))
                    cd "${HISTORY[$HISTORY_POS]}"
                    CURRENT_DIR=$(pwd)
                    SELECTED_ITEM=0
                    CURRENT_PAGE=0
                fi
                ;;
            g)
                # Přejít na začátek seznamu
                SELECTED_ITEM=0
                CURRENT_PAGE=0
                ;;
            G)
                # Přejít na konec seznamu
                SELECTED_ITEM=$((${#items[@]} - 1))
                CURRENT_PAGE=$(((${#items[@]} - 1) / ITEMS_PER_PAGE))
                ;;
            $'\033')
                # Escape sekvence pro speciální klávesy
                read -n 2 -t 0.1 rest
                case "$rest" in
                    "[5")
                        # Page Up
                        read -n 1 -t 0.1 tmp
                        if [ $CURRENT_PAGE -gt 0 ]; then
                            CURRENT_PAGE=$((CURRENT_PAGE - 1))
                            SELECTED_ITEM=$((CURRENT_PAGE * ITEMS_PER_PAGE))
                        fi
                        ;;
                    "[6")
                        # Page Down
                        read -n 1 -t 0.1 tmp
                        if [ $CURRENT_PAGE -lt $(((${#items[@]} - 1) / ITEMS_PER_PAGE)) ]; then
                            CURRENT_PAGE=$((CURRENT_PAGE + 1))
                            SELECTED_ITEM=$((CURRENT_PAGE * ITEMS_PER_PAGE))
                        fi
                        ;;
                    "[H")
                        # Home - přejít do domovského adresáře
                        cd ~
                        CURRENT_DIR=$(pwd)
                        SELECTED_ITEM=0
                        CURRENT_PAGE=0
                        add_to_history "$CURRENT_DIR"
                        ;;
                esac
                ;;
            e)
                # Upravit soubor
                local selected="${items[$SELECTED_ITEM]}"
                if [ -f "$selected" ]; then
                    edit_file "$selected"
                fi
                ;;
            v)
                # Zobrazit soubor
                local selected="${items[$SELECTED_ITEM]}"
                if [ -f "$selected" ]; then
                    if command -v less &> /dev/null; then
                        less "$selected"
                    else
                        cat "$selected" | more
                    fi
                fi
                ;;
        esac
    done
}

# Spustit hlavní funkci
main
