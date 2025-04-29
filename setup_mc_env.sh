#!/bin/bash
# Skript pro nastavení proměnných prostředí pro Midnight Commander

echo "=== Nastavení proměnných prostředí pro Midnight Commander ==="
echo ""

# Hledání instalace mc
echo "Hledám instalaci Midnight Commander..."
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

# Nastavení proměnných prostředí
echo "Nastavuji proměnné prostředí..."

# Přidání do .bashrc
echo "Přidávám nastavení do ~/.bashrc..."
cat >> ~/.bashrc << EOF

# Nastavení pro Midnight Commander
export TERM=xterm-256color
export COLORTERM=truecolor
export TERMINFO=/usr/share/terminfo
alias mc="$MC_PATH -d"
EOF

# Přidání do .profile
echo "Přidávám nastavení do ~/.profile..."
cat >> ~/.profile << EOF

# Nastavení pro Midnight Commander
export TERM=xterm-256color
export COLORTERM=truecolor
export TERMINFO=/usr/share/terminfo
EOF

# Vytvoření skriptu pro spouštění mc
echo "Vytvářím skript pro spouštění mc..."
cat > ~/mc_env.sh << EOF
#!/bin/bash
export TERM=xterm-256color
export COLORTERM=truecolor
export TERMINFO=/usr/share/terminfo
$MC_PATH -d "\$@"
EOF

chmod +x ~/mc_env.sh

# Vytvoření konfiguračního adresáře pro mc
echo "Vytvářím konfigurační adresář pro mc..."
mkdir -p ~/.config/mc

# Vytvoření základní konfigurace
echo "Vytvářím základní konfiguraci..."
cat > ~/.config/mc/ini << EOF
[Midnight-Commander]
verbose=true
shell_patterns=true
auto_save_setup=true
auto_menu=false
use_internal_view=true
use_internal_edit=true
clear_before_exec=true
confirm_delete=true
confirm_overwrite=true
confirm_execute=false
confirm_exit=false
confirm_directory_hotlist_delete=true
confirm_view_dir=false
safe_delete=false
use_8th_bit_as_meta=false
mouse_move_pages_viewer=true
mouse_close_dialog=false
fast_refresh=false
drop_menus=false
wrap_mode=true
old_esc_mode=false
cd_symlinks=true
show_all_if_ambiguous=false
use_file_to_guess_type=true
alternate_plus_minus=false
only_leading_plus_minus=true
show_output_starts_shell=false
panel_scroll_pages=true
xtree_mode=false
num_history_items_recorded=60
file_op_compute_totals=true
classic_progressbar=true
use_netrc=true
auto_hint_lines=2
auto_fill_mkdir_name=true
copymove_persistent_attr=true
select_flags=6
editor_backup_extension=~
mcview_eof=
ignore_ftp_chattr_errors=true
skin=default
filepos_max_saved_entries=1024

[Layout]
message_visible=false
keybar_visible=true
xterm_title=true
output_lines=0
command_prompt=true
menubar_visible=true
free_space=true
horizontal_split=false
vertical_equal=true
left_panel_size=80
horizontal_equal=true
top_panel_size=1

[Misc]
timeformat_recent=%b %e %H:%M
timeformat_old=%b %e  %Y
ftp_proxy_host=gate
ftpfs_password=anonymous@
display_codepage=UTF-8
source_codepage=Other_8_bit
autodetect_codeset=
spell_language=en
clipboard_store=
clipboard_paste=

[Colors]
base_color=
xterm-256color=
color_terminals=

xterm=

[Panels]
show_mini_info=true
kilobyte_si=false
mix_all_files=false
show_backups=true
show_dot_files=true
fast_reload=false
fast_reload_msg_shown=false
mark_moves_down=true
reverse_files_only=true
auto_save_setup_panels=false
navigate_with_arrows=false
panel_scroll_center=false
mouse_move_pages=true
filetype_mode=true
permission_mode=false
torben_fj_mode=false
quick_search_mode=2
select_flags=6

simple_swap=false

[Panelize]
Find *.orig after patching=find . -name \\*.orig -print
Find SUID and SGID programs=find . \\( \\( -perm -04000 -a -perm /011 \\) -o \\( -perm -02000 -a -perm /01 \\) \\) -print
Find rejects after patching=find . -name \\*.rej -print
Modified git files=git ls-files --modified
EOF

echo ""
echo "=== Nastavení dokončeno ==="
echo "Midnight Commander můžete spustit následujícími způsoby:"
echo "1. Po načtení aliasů (source ~/.bashrc): mc"
echo "2. Pomocí skriptu: ~/mc_env.sh"
echo ""
echo "Pro aplikaci změn v aktuální relaci spusťte:"
echo "source ~/.bashrc"
