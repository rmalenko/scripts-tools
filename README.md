# Various scripts may be helpful or not :)

[**cloud_flare_stats_json_graphql.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/cloud_flare_stats_json_graphql.py) - The script get the list of domains from HostTracker as the primary source, then looking these domains in Cloudflare and gets statistic by domain from CF using graphql requests Add to the JSON file the Uptime value from HostTracker and the status of Borg backup from Prometheus. We need to set up crontab to run this script every 0: 05 each month on the first day Then we can calculate the previous month's first and last days

[**hetzner_get_host_ip_to_ansible.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/hetzner_get_host_ip_to_ansible.py) - This script is used to get the server's IPs from Hetzner cloud and create a hosts.yml file for ansible. It imports the hcloud, yaml, and token modules. A client object is created using the token and all running servers are retrieved from the client object. The ansiblehosts function is then used to collect and update a dictionary with values from the servers. which is then added to a header_dict. Finally, a hosts_hetzner.yml file is written with the header_dict using yaml dump

[**host-tracker.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/host-tracker.py)  - Unfinished. Should create a Grafana dashboard snaps.

[**do-firewal-monitors.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/do-firewal-monitors.py) - This script gets a list of allowed droplet IDs from a firewall name and compares this list with a predefined list of allowed droplet IDs And send email using SendGrid

[**hetzner_list_servers.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/hetzner_list_servers.py) - This script is used to get the server's name from Hetzner cloud and create a hosts_hetzner.txt.

[**prometheus_query.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/prometheus_query.py) - This script collects Cloudflare metrics from Prometheus using the domain list from Host Tracker as the primary source of hosted domains

[**dutop.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/dutop.py) - Show top disk space users in current directory, while automatically recursing down directories if there is one obvious directory using the space

[**host-tracker-list-zones-yaml.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/host-tracker-list-zones-yaml.py) - Generate domain list in YAML file for Prometheus domainexporter

[**ps_mem.py**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/ps_mem.py) - Try to determine how much RAM is currently being used per program.


[**borg_backup_staging_new.sh**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/borg_backup_staging_new.sh) - This script creates separated backups per project, specifically volume uploads and MySQL dumps. It initially sets up variables such as the location and format of the backup storage, and the number of backups to keep. It then sets up variables for various email settings and metrics settings, and starts the process of checking backups for consistency. The script then creates and uploads a backup of each project's docker container volume and creates a MySQL database dump file for each project that is then uploaded to the backup server. Subsequently, the script checks the last four archives for consistency and sends an email if errors are found. Finally, the script sends metrics into Prometheus

[**tag_all_droplets.sh**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/tag_all_droplets.sh) - Add a tag to DigitalOcean droplets.

[**ssh_email_new_login.sh**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/ssh_email_new_login.sh) - The script sends an alert if the new SSH login isn't from jump.domain.com. Copy it into `/etc/profile.d`

[**scripts-tools/0/restore_backup_staging.sh**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/scripts-tools/0/restore_backup_staging.sh) - The script will restore only volume of uploads folder or MySQL DB or both.

[**send-wp-plugin-metrics.sh**](https://github.com/rmalenko/scripts-tools/blob/main/scripts/scripts-tools/0/send-wp-plugin-metrics.sh) - Collect some WordPress information of plugins and send them to Prometheus.
