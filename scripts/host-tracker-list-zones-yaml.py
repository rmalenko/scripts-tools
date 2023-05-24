#!/usr/bin/env python3

# Generate domain list in YAML file for Prometheus domainexporter

# License: LGPLv2
# Author: <rmalenko+github@gmail.com>

import re
import yaml
import contextlib
import sys
import os
import json
import requests
from requests.structures import CaseInsensitiveDict

sys.path.insert(0, os.path.abspath('..'))

reports_dir = "./reports"
zonefile = f"{reports_dir}/zones.txt"

with contextlib.suppress(FileExistsError):
    os.makedirs(reports_dir)

with contextlib.suppress(OSError):
    os.remove(zonefile)


def replace(string, substitutions):
    substrings = sorted(substitutions, key=len, reverse=True)
    regex = re.compile('|'.join(map(re.escape, substrings)))
    return regex.sub(lambda match: substitutions[match.group(0)], string)


# get authorization token for requests to other API
url_ht_token = "https://www.host-tracker.com/api/web/v1/users/token"
headers_ht = CaseInsensitiveDict()
headers_ht["User-Agent"] = "Fiddler"
headers_ht["Content-Type"] = "application/json"
headers_ht["Host"] = "www.host-tracker.com"
data_ht = '{"login":"login","password":"password"}'

# get authorization token for requests to other API
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
responce_ht = (json.loads(domain.text))


def domain_yaml():
    domains_json = responce_ht
    for item in domains_json:
        yield re.sub('http(s)?(:)?(//)?|(//)?(www.)?', "", item['url'])


with open(f"{reports_dir}/domains.yaml", 'w') as outfile:
    outfile.write(yaml.dump([{"targets": list(domain_yaml())}],
                  explicit_start=True, default_flow_style=False))
