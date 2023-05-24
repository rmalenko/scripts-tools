#!/usr/bin/env python3

# pip3 install hcloud

# This script is used to get the server's IPs from Hetzner cloud and create a hosts.yml file for ansible.
# It imports the hcloud, yaml, and token modules.
# A client object is created using the token and all running servers are retrieved from the client object.
# The ansiblehosts function is then used to collect and update a dictionary with values from the servers,
# which is then added to a header_dict. Finally, a hosts_hetzner.yml file is written with the header_dict using yaml dump.

# License: LGPLv2
# Author: <rmalenko+github@gmail.com>


# from hcloud import Client
import hcloud
import yaml

token = "hLC"

# client object created using the token
client = hcloud.Client(token=token)

# get all servers from the client object
servers = client.servers.get_all(status='running')


def ansiblehosts():
    for server in servers:
        yield {server.name: {"ansible_port": 22, "ansible_host": server.public_net.ipv4.ip}}


# Collect and update dictionary adding values from ansiblehosts
host_dict = {}
for hosts in ansiblehosts():
    host_dict.update(hosts)

# Update dictionary adding to header_dict
header_dict = {"hetzner": {"hosts": {}}}
header_dict["hetzner"]["hosts"].update(host_dict)

# open a file in write mode
with open("hosts_hetzner.yml", "w") as hosts_file:
    hosts_file.write(yaml.dump(header_dict))
    hosts_file.close()
