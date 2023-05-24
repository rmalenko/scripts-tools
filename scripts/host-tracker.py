#!/usr/bin/env python3

# License: LGPLv2
# Author: <rmalenko+github@gmail.com>
# append output data from Grafana with URL to snaps.

import re
import errno
import contextlib
import sys
import os
import json
import ast
import requests
from requests.structures import CaseInsensitiveDict
import CloudFlare

# Curl requests
url = "http://localhost:8080/api/snapshots"
headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer glsa_Wn"

clodflare_token = "vCG7"
zonefile = "zones.txt"
dashboard_template = "report_001.json"
sys.path.insert(0, os.path.abspath('..'))

reports_dir = "./reports"
jsontemplate = '{"zone_tmp": []}'

with contextlib.suppress(FileExistsError):
    os.makedirs(reports_dir)

with contextlib.suppress(OSError):
    os.remove(zonefile)


# Get zones from Cloudflare and write into file
def main():
    # Grab the first argument, if there is one
    try:
        zone_name = sys.argv[1]
        params = {'name': zone_name, 'per_page': 1}
    except IndexError:
        params = {'per_page': 50}

    # An authenticated call using an API Token (note the missing email)
    cf = CloudFlare.CloudFlare(
        token=clodflare_token)

    # grab the zone identifier
    try:
        zones = cf.zones.get(params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit('/zones %d %s - api call failed' % (e, e))
    except Exception as e:
        exit(f'/zones.get - {e} - api call failed11')

    # there should only be one zone
    for zone in sorted(zones, key=lambda v: v['name']):
        zone_name = zone['name']
        with open(zonefile, "a") as file:
            print(f'{zone_name}', file=file)
    # exit(0)


if __name__ == '__main__':
    main()


# I use jsontemplate replace "zone_tmp" into zone (domain) and append output data from Grafana with URL to snaps.
# Then save it to separate files.
def write_json(new_data, newzonejsn, filename):
    json_data = ast.literal_eval(jsontemplate.replace('zone_tmp', newzonejsn))
    json_data[newzonejsn].append(new_data)
    # print(json_data)
    # convert back to json.
    json_object = json.dumps(json_data, indent=4)
    with open(filename, "w") as outfile:
        outfile.write(json_object)


# There we I open zone file with list of zones (domains) then replace "replace_zone" into zone (domain) in Grafana dashboard template.
# After that send CURL request to Grafana with template and get TEXT output which I use to create JSON files.
with open(zonefile, 'r') as zone_file:
    for zone in zone_file.read().split('\n'):
        with open(dashboard_template, 'r') as templatefile:
            template = templatefile.read()
            data = template.replace('replace_zone', zone)
            resp = requests.post(url, headers=headers, data=data)
            data_snap = ast.literal_eval(resp.text)
            write_json(new_data=data_snap, newzonejsn=zone,
                       filename=(f"{reports_dir}/snaps_{zone}.json"))
