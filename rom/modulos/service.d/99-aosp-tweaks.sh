#!/system/bin/sh
# Ajustes conservadores para o Tab A7 Lite MT8768.
# Mantem a politica de memoria para ZRAM sem alterar o frame pacing.
sysctl -w vm.swappiness=100
sysctl -w vm.vfs_cache_pressure=100
sysctl -w vm.dirty_ratio=20
sysctl -w vm.dirty_background_ratio=5
setprop wifi.supplicant_scan_interval 180
setprop persist.sys.use_dithering 0
