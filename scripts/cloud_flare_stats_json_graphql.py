#!/usr/bin/env python3

# The script get the list of domains from HostTracker as the primary source, then looking
# these domains in Cloudflare and gets statistic by domain from CF using graphql requests.
# Add to the JSON file the Uptime value from HostTracker and the status of Borg backup from
# Prometheus. We need to set up crontab to run this script every 0: 05 each month on the first day.
# Then we can calculate the previous month's first and last days.

# License: LGPLv2
# Author: <rmalenko+github@gmail.com>

from requests.structures import CaseInsensitiveDict
import urllib.parse
import requests
import contextlib
import json
import re
import pytz
import datetime
import time
import sys
import os
import CloudFlare
import sendgrid  # pip3 install sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from prometheus_api_client import PrometheusConnect

# for debug
# import logging
# logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# HT - add sleep time for each new request``
pause = 5

# Collect statistics from Cloud Flare by domain and output it to JSON a file
# pip install cloudflare
# https://cfdata.lol/graphql/
# https://pages.johnspurlock.com/graphql-schema-docs/cloudflare.html

# API calls quota exceeded! maximum admitted 1 per Second.

sys.path.insert(0, os.path.abspath('..'))

reports_dir = "./public/json"
websites = "websites.txt"

last_day_of_prev_month = datetime.date.today().replace(day=1) - \
    datetime.timedelta(days=1)
start_day_of_prev_month = datetime.date.today().replace(
    day=1) - datetime.timedelta(days=last_day_of_prev_month.day)

# print('First day of prev month:', start_day_of_prev_month)
# print('Last day of previous month:', last_day_of_prev_month)

with contextlib.suppress(FileExistsError):
    os.makedirs(reports_dir)

# Send e-mail if an error
sg = sendgrid.SendGridAPIClient(
    api_key='SG.5dr')
from_email = Email("M L <devops@domain.com>")
to_email = To("6@tasks.teamwork.com")
subject = "🔥 !! Cloudflare statistic ERROR to getting"


# Get zone list from HostTracker
###################################################
# Delete old zone file

with contextlib.suppress(OSError):
    os.remove(f"{reports_dir}/{websites}")

# get authorization token for requests to other API
url_ht_token = "https://www.host-tracker.com/api/web/v1/users/token"
headers_ht = CaseInsensitiveDict()
headers_ht["User-Agent"] = "Fiddler"
headers_ht["Content-Type"] = "application/json"
headers_ht["Host"] = "www.host-tracker.com"
data_ht = '{"login":"login","password":"passwd"}'


def ht_ticket():
    ticket = requests.post(url_ht_token, headers=headers_ht, data=data_ht)
    responce = (json.loads(ticket.text))
    return responce['ticket']


# get all domain in the account
url_ht_tasks = "https://www.host-tracker.com/api/web/v1/tasks"
headers_htasks = CaseInsensitiveDict()
headers_htasks["User-Agent"] = "Fiddler"
headers_htasks["Accept"] = "application/json"
headers_htasks["Host"] = "www.host-tracker.com"
headers_htasks["Authorization"] = "Bearer " f'{ht_ticket()}'

domain = requests.get(url_ht_tasks, headers=headers_htasks)
responce_ht = json.loads(domain.text)
for item in responce_ht:
    with open(f"{reports_dir}/{websites}", 'a') as outfile:
        outfile.writelines(item['url'] + "\n")
        # outfile.writelines(re.sub('http(s)?(:)?(//)?|(//)?(www.)?', "", item['url']) + "\n") # remove https://


# Prometheus connection IP
url_prometheus = "http://1.2.3.4:9090"
prom = PrometheusConnect(
    url=url_prometheus, disable_ssl=True)
job_name = "donodeexporter"


# Prometheus. Get Borg backup status. Data in Prometheus delivers ./files/borg_check_consistency.sh
# Backup borg consistency
def borg_backup(job, zone):
    borg_backup = prom.custom_query(
        query="last_over_time(borg_backup_consistency{job='"f'{job}'"',zone='"f'{zone}'"'}[24h])"
    )
    for domain_z in borg_backup:
        # domain_zone = domain_z['metric']['zone']
        return domain_z['value'][1]
        # return {domain_zone: domain_z['value'][1]}


# Cloud Flare
###################################################
# A minimal call - reading values from environment variables or configuration file
cf = CloudFlare.CloudFlare()

# A minimal call with debug enabled
cf = CloudFlare.CloudFlare(debug=True)

# An authenticated call using an API Token (note the missing email)
cf = CloudFlare.CloudFlare(token='I7')


def zone_id():
    try:
        # Grab the zone name
        try:
            zone_name = sys.argv[1]
            params = {'name': zone_name, 'per_page': 1}
        except IndexError:
            params = {'per_page': 500}

        # grab the zone identifier
        try:
            zones = cf.zones.get(params=params)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones.get %d %s - api call failed' % (e, e))
        except Exception as e:
            exit(f'/zones - {e} - api call failed')

        # HostTracker is the primary source of domains(URLs). It means we should find the same domains on Cloudflare.
        # I.e., we don't need to parse all domains in CloudFalre.
        # Open previously generated from HostTracker zones list file.

        with open(f"{reports_dir}/{websites}", 'r') as zone_ht_file:
            for zone_ht in zone_ht_file:
                # strip out all tailing whitespace
                zone_url = zone_ht.rstrip('\r\n')
                zone_url_without_www = re.sub(
                    'http(s)?(:)?(//)?|(//)?(www.)?', "", zone_ht.rstrip('\r\n'))

                for zone in sorted(zones, key=lambda v: v['name']):
                    # zone_url from HostTracker. Checks if the zone from Host Tracker is present in JSON output from CloudFlare
                    if zone_url_without_www in zone['name']:
                        zone_name = zone['name']
                        zone_plan = zone['plan']['name']
                        zone_id_list = zone['id']
                        borg_backup_status = borg_backup(
                            job=job_name, zone=zone_name)

                        urlparams = {'taskType': 'Http', 'url': zone_url,
                                     'statsStart': start_day_of_prev_month, 'statsEnd': last_day_of_prev_month}
                        url_ht_stats = f"https://www.host-tracker.com/api/web/v1/stats?{urllib.parse.urlencode(urlparams)}"
                        uptime_ht = requests.get(
                            url_ht_stats, headers=headers_htasks)
                        responce_uptime_ht = json.loads(uptime_ht.text)
                        # print(zone_url)
                        # print(url_ht_stats)
                        # print(responce_uptime_ht)

                        with contextlib.suppress(Exception):
                            uptime_output = responce_uptime_ht['stats'][0]['uptimePercent']
                            time.sleep(pause)

                        query = """
                            query {
                                viewer {
                                    zones(filter: {zoneTag: "%s"}) {
                                        httpRequests1dGroups(orderBy: [date_ASC], limit: 500, filter: {date_leq: "%s", date_geq: "%s"}) {
                                            dimensions {
                                                date
                                            }
                                            sum {
                                                browserMap {
                                                    pageViews
                                                    uaBrowserFamily
                                                }
                                                requests
                                                bytes
                                                cachedBytes
                                                cachedRequests
                                                pageViews
                                                requests
                                                threats
                                                countryMap {
                                                    bytes
                                                    requests
                                                    threats
                                                    clientCountryName
                                                }
                                                threatPathingMap {
                                                    requests
                                                    threatPathingName
                                                }
                                            }
                                            uniq {
                                                uniques
                                            }
                                        }
                                    }
                                }
                            }
                        """ % (zone_id_list, last_day_of_prev_month, start_day_of_prev_month)  # only use yyyy-mm-dd part for httpRequests1dGroups

                        # query - always a post
                        try:
                            r = cf.graphql.post(data={'query': query})
                        except CloudFlare.exceptions.CloudFlareAPIError as e:
                            exit('/graphql.post %d %s - api call failed' % (e, e))

                        # only one zone, so use zero'th element!
                        zone_info = r['data']['viewer']['zones'][0]

                        # add to JSON key = domain name and additional key/value
                        # borg_status = 0 it means OK. NULL backup doesn't enabled, not found, 1 = has an error
                        output_zones = {f'{zone_name}': {
                            'plan': zone_plan, 'uptime_percent': uptime_output, 'borg_status': borg_backup_status}}
                        output_zones[zone_name].update(zone_info)

                        with open(f"{reports_dir}/{zone_name}_cf_summary_report_{last_day_of_prev_month}.json", 'w') as outfile:
                            outfile.write(json.dumps(output_zones, indent=4))

    except Exception as e:
        # exit(f'Get statistic - {e} - api call failed')
        content = Content(
            'text/plain', f'ERROR getting Cloudflare statistic.\n The script stopped with error: {e}.\n It means we may only have an incomplete statistic. Some domains may be absent. You should run the script manually to check.')
        mail = Mail(from_email, to_email, subject, content)
        mail_json = mail.get()
        # response = sg.client.mail.send.post(request_body=mail_json)
        exit(sg.client.mail.send.post(request_body=mail_json))
        print(content)

    # exit(0)


zone_id()
