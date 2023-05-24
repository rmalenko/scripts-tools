# Various scripts may be helpful or not :)

**cloud_flare_stats_json_graphql.py** - The script get the list of domains from HostTracker as the primary source, then looking these domains in Cloudflare and gets statistic by domain from CF using graphql requests Add to the JSON file the Uptime value from HostTracker and the status of Borg backup from Prometheus. We need to set up crontab to run this script every 0: 05 each month on the first day Then we can calculate the previous month's first and last days

**hetzner_get_host_ip_to_ansible.py** - # This script is used to get the server's IPs from Hetzner cloud and create a hosts.yml file for ansible. It imports the hcloud, yaml, and token modules. A client object is created using the token and all running servers are retrieved from the client object. The ansiblehosts function is then used to collect and update a dictionary with values from the servers. which is then added to a header_dict. Finally, a hosts_hetzner.yml file is written with the header_dict using yaml dump

**host-tracker.py**  - Unfinished. Should create a Grafana dashboard snaps.

**do-firewal-monitors.py** - This script gets a list of allowed droplet IDs from a firewall name and compares this list with a predefined list of allowed droplet IDs And send email using SendGrid

**hetzner_list_servers.py** - This script is used to get the server's name from Hetzner cloud and create a hosts_hetzner.txt.

**prometheus_query.py**  - This script collects Cloudflare metrics from Prometheus using the domain list from Host Tracker as the primary source of hosted domains

**dutop.py** - # Show top disk space users in current directory, while automatically recursing down directories if there is one obvious directory using the space

**host-tracker-list-zones-yaml.py** - Generate domain list in YAML file for Prometheus domainexporter

**ps_mem.py** - Try to determine how much RAM is currently being used per program.
