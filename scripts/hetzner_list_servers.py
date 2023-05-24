#!/usr/bin/env python3

# pip3 install hcloud

# This script is used to get the server's name from Hetzner cloud and create a hosts_hetzner.txt.

# License: LGPLv2
# Author: <rmalenko+github@gmail.com>

# from hcloud import Client
import hcloud
import re

token = "hLC"
exlude_servers_list = '(mon-prometheus-hetzner.*|.*mysql.*)'
# client object created using the token
client = hcloud.Client(token=token)
# get all servers from the client object
servers = client.servers.get_all(status='running')


def hezner_servers():
    for server in servers:
        yield re.sub(exlude_servers_list, "", server.name)


# filter out empty strings and save the list of servers to a variable
servers_list = list(filter(None, hezner_servers()))

# open a file to write the list of servers to it
with open("/tmp/lists_hosts_on_hetzner.txt", "w") as hosts_file:
    for item in servers_list:  # write each item from the list to the file
        hosts_file.write(f"{item}\n")
    hosts_file.close()  # close the file when done writing
