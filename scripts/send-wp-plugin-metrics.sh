#!/bin/bash

# Collect some WordPress information of plugins and send them to Prometheus.

node_exporter_collector_directory="/custom-metrics"
domain="$(wp --allow-root --path=/var/www option get home | sed 's|https://||')";
wp_version="$(wp --allow-root --path=/var/www core version)";
php_version="$(wp --allow-root --path=/var/www cli info | awk 'FNR == 4 {print $3}')";

# Create file for nodeexporter wit string in Prometheus format with random extension
wp --allow-root --path=/var/www plugin list --status=active --format=json | jq -r --arg dmn "${domain}" --arg wpver "${wp_version}" 'to_entries[] | (if .value.update == "available" then 1 else 0 end) as $v | .value | to_entries | map("\(.key)=\(.value|@json)") | join(",") | "wp_plugins{\(.),domain=\"\($dmn)\",wpver=\"\($wpver)\"}\($v)"' >> "${node_exporter_collector_directory}/plugins_${domain}.prom.$$"
printf 'wp_version{wpver="%s",phpversion="%s",domain="%s"}%s\n' "${wp_version}" "${php_version}" "${domain}" "${wp_version//.}" >> "${node_exporter_collector_directory}/wp_version_${domain}.prom.$$"

# Remove old files with data
[[ -f "${node_exporter_collector_directory}/plugins_${domain}.prom" ]] && rm "${node_exporter_collector_directory}/plugins_${domain}.prom"
[[ -f "${node_exporter_collector_directory}/wp_version_${domain}.prom" ]] && rm "${node_exporter_collector_directory}/wp_version_${domain}.prom"

# Rename new files extensions to .prom. Nodeexporter looking for file with this extension .prom
mv "${node_exporter_collector_directory}/plugins_${domain}.prom.$$" "${node_exporter_collector_directory}/plugins_${domain}.prom"
mv "${node_exporter_collector_directory}/wp_version_${domain}.prom.$$" "${node_exporter_collector_directory}/wp_version_${domain}.prom"
