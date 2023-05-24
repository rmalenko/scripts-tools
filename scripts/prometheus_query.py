#!/usr/bin/env python3

# This script collects Cloudflare metrics from Prometheus using the domain
# list from Host Tracker as the primary source of hosted domains.
# https: // github.com/lablabs/cloudflare-exporter

# License: LGPLv2
# Author: <rmalenko+github@gmail.com>

# Needs to install prometheus-api-client, mergedeep
# https: // pypi.org/project/mergedeep/
# https://github.com/4n4nd/prometheus-api-client-python

from prometheus_api_client import PrometheusConnect
import json
import calendar
import datetime
import contextlib
import os
# https://github.com/clarketm/mergedeep pip3 install mergedeep
from mergedeep import merge

# Prometheus connection IP
prom = PrometheusConnect(
    url="http://1.2.3.4:9090", disable_ssl=True)

now = datetime.datetime.now()
# return the number of days of the current month
interval_days = calendar.monthrange(now.year, now.month)[1]
# Top 10
topk = 10

reports_dir = "./reports"

with contextlib.suppress(FileExistsError):
    os.makedirs(reports_dir)


# Uptime
def uptime_percent():
    uptime_data = prom.custom_query(
        query="avg_over_time(host_tracker_uptime_percent{job='donodeexporter'}["f'{interval_days}'"d])"
    )
    for domain_z in uptime_data:
        domain_zone = domain_z['metric']['zone']
        uptime = domain_z['value'][1]
        yield {domain_zone: {'uptime': uptime}}


# Cloudflare threats total by zone
def cloudflare_threats():
    cloudflare_threats_total = prom.custom_query(
        query="sum by(zone) (increase(cloudflare_zone_threats_total{job='cloudflare'}["f'{interval_days}'"d]))"
    )
    for domain_z in cloudflare_threats_total:
        domain_zone = domain_z['metric']['zone']
        threats_number = domain_z['value'][1]
        yield {domain_zone: {'threats': threats_number}}


# Cloudflare zone requests total by zone
def cloudflare_zone_rqst():
    cloudflare_zone_requests = prom.custom_query(
        query="sum by(zone) (increase(cloudflare_zone_requests_total{job='cloudflare'}["f'{interval_days}'"d]))"
    )
    for domain_z in cloudflare_zone_requests:
        domain_zone = domain_z['metric']['zone']
        threats_number = domain_z['value'][1]
        yield {domain_zone: {'requests_total': threats_number}}


# Cloudflare zone requests uniques by zone
def cloudflare_uniq_total():
    cloudflare_uniques_total = prom.custom_query(
        query="sum by(zone) (increase(cloudflare_zone_uniques_total{job='cloudflare'}["f'{interval_days}'"d]))"
    )
    for domain_z in cloudflare_uniques_total:
        domain_zone = domain_z['metric']['zone']
        value_number = domain_z['value'][1]
        yield {domain_zone: {'uniques_total': value_number}}

# Cloudflare pageviews total
def cloudflare_pageviews_total():
    cloudflare_pageviews = prom.custom_query(
        query="sum by(zone) (increase(cloudflare_zone_pageviews_total{job='cloudflare'}["f'{interval_days}'"d]))"
    )
    for domain_z in cloudflare_pageviews:
        domain_zone = domain_z['metric']['zone']
        value_number = domain_z['value'][1]
        yield {domain_zone: {'pageviews_total': value_number}}


# Cloudflare requests cached
def cloudflare_requests_cached():
    cloudflare_requests = prom.custom_query(
        query="sum by(zone) (increase(cloudflare_zone_requests_cached{job='cloudflare'}["f'{interval_days}'"d]))"
    )
    for domain_z in cloudflare_requests:
        domain_zone = domain_z['metric']['zone']
        value_number = domain_z['value'][1]
        yield {domain_zone: {'requests_cached': value_number}}


# Cloudflare zone bandwidth total
def cloudflare_bandwidth_total():
    cloudflare_bandwidth = prom.custom_query(
        query="sum by(zone) (increase(cloudflare_zone_bandwidth_total{job='cloudflare'}["f'{interval_days}'"d]))"
    )
    for domain_z in cloudflare_bandwidth:
        domain_zone = domain_z['metric']['zone']
        value_number = domain_z['value'][1]
        yield {domain_zone: {'bandwidth_total': value_number}}


# Backup borg consistency
def borg_backup():
    borg_backup = prom.custom_query(
        query="last_over_time(borg_backup_consistency{job='donodeexporter'}[24h])"
    )
    for domain_z in borg_backup:
        domain_zone = domain_z['metric']['zone']
        value_number = domain_z['value'][1]
        yield {domain_zone: {'borg_backup': value_number}}


# Convert a Nested List Into a Dictionary
result_uptime = {a: b for i in list(uptime_percent()) for a, b in i.items()}
result_threats = {a: b for i in list(
    cloudflare_threats()) for a, b in i.items()}
result_zone_rqst = {a: b for i in list(
    cloudflare_zone_rqst()) for a, b in i.items()}
result_uniques_total = {a: b for i in list(
    cloudflare_uniq_total()) for a, b in i.items()}
result_pageviews_total = {a: b for i in list(
    cloudflare_pageviews_total()) for a, b in i.items()}
result_requests_cached = {a: b for i in list(
    cloudflare_requests_cached()) for a, b in i.items()}
result_bandwidth_total = {a: b for i in list(
    cloudflare_bandwidth_total()) for a, b in i.items()}
result_borg_backup = {a: b for i in list(borg_backup()) for a, b in i.items()}


result_dict = {"total_stats": merge(result_uptime, result_threats, result_zone_rqst, result_uniques_total,
                                    result_pageviews_total, result_requests_cached, result_bandwidth_total, result_borg_backup)}

# print(json.dumps(result_dict))
with open(f"{reports_dir}/summary_report.json", 'w') as outfile:
    outfile.write(json.dumps(result_dict, indent=4))


# Requests browser page views count Top-10 for domain
def browser_map_page_views(domain_zone):
    cloudflare = prom.custom_query(
        query="topk("f'{topk}'", sum by(family) (increase(cloudflare_zone_requests_browser_map_page_views_count{job='cloudflare', zone='"f'{domain_zone}'"'}["f'{interval_days}'"d])))"
    )
    for domain_z in cloudflare:
        user_agent = domain_z['metric']['family']
        value = domain_z['value'][1]
        yield {domain_zone: {user_agent: value}}


# Threats by region Top-10 for domain
def cloudflare_zone_threats_country(domain_zone):
    cloudflare = prom.custom_query(
        query="topk by(region) ("f'{topk}'", sum by(region) (increase(cloudflare_zone_threats_country{job='cloudflare', zone='"f'{domain_zone}'"'}["f'{interval_days}'"d])) != 0)"
    )
    for domain_z in cloudflare:
        user_agent = domain_z['metric']['region']
        value = domain_z['value'][1]
        yield {domain_zone: {user_agent: value}}


# Requests by country Top-10 for ddomain
def cloudflare_zone_requests_country(domain_zone):
    cloudflare = prom.custom_query(
        query="topk("f'{topk}'", sum by(country) (increase(cloudflare_zone_requests_country{job='cloudflare', zone='"f'{domain_zone}'"'}["f'{interval_days}'"d])) != 0)"
    )
    for domain_z in cloudflare:
        user_agent = domain_z['metric']['country']
        value = domain_z['value'][1]
        yield {domain_zone: {user_agent: value}}


# Get list of zones from Prometheus based on Host Tracker data
def domain_zones():
    zones_domain = prom.custom_query(
        query="host_tracker_uptime_percent{job='donodeexporter'}"
    )
    for domain_z in zones_domain:
        yield domain_z['metric']['zone']


# Get a list of domains and substitution each one into a request of Prometheus query.
def collect_data(query):
    for domain_list in domain_zones():
        # yield list(browser_map_page_views(domain_zone=domain_list))
        yield list(query(domain_zone=domain_list))


# Return data after yield iteration
def return_cloud_flare_data(data_collect):
    return list(collect_data(query=data_collect))


# Output Requests browser page views count Top-10 for domain
with open(f"{reports_dir}/browser_map_page_views.json", 'w') as outfile:
    outfile.write(json.dumps(return_cloud_flare_data(
        data_collect=browser_map_page_views), indent=4))

# Output Threats by region Top-10 for domain
with open(f"{reports_dir}/zone_threats_country.json", 'w') as outfile:
    outfile.write(json.dumps(return_cloud_flare_data(
        data_collect=cloudflare_zone_threats_country), indent=4))

# Requests by country Top-10 for ddomain
with open(f"{reports_dir}/zone_requests_country.json", 'w') as outfile:
    outfile.write(json.dumps(return_cloud_flare_data(
        data_collect=cloudflare_zone_requests_country), indent=4))


#  Total WP plugins
def wp_plugins(status, update):
    wpplugins = prom.custom_query(
        query="min by(name, domain, version, wpver) (last_over_time(wp_plugins{status='"f'{status}'"', update=~'"f'{update}'"'}[1h]))"
    )
    for plugin in wpplugins:
        plugin_domain = plugin['metric']['domain']
        plugin_name = plugin['metric']['name']
        plugin_version = plugin['metric']['version']
        # 1 means an update available. 0 no updates
        plugin_update_status = plugin['value'][1]
        wp_version = plugin['metric']['wpver']
        wpdict = {'plugin_name': plugin_name, 'plugin_version': plugin_version,
                  'wp_version': wp_version, 'plugin_update_status': plugin_update_status}
        output = {}
        output[plugin_domain] = output.get(plugin_domain, {})
        output[plugin_domain].update(wpdict)
        yield output


wp_plugins_all_active = list(wp_plugins(
    status='active', update='(none|available)'))

print(json.dumps(wp_plugins_all_active, indent=4))

with open(f"{reports_dir}/wp_plugins_stats.json", 'w') as outfile:
    outfile.write(json.dumps(
        list(wp_plugins(status='active', update='(none|available)')), indent=4))
