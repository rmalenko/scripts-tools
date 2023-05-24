#!/usr/bin/env python3

# This script gets a list of allowed droplet IDs from a firewall name and compares this list with
# a predefined list of allowed droplet IDs.
# And send email using SendGrid

# License: LGPLv2
# Author: <rmalenko+github@gmail.com>

from requests.structures import CaseInsensitiveDict
import requests
import sendgrid  # pip3 install sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

# Needs to imrove the security.
token = "dop_v1_"
# api url
url_droplets = "https://api.digitalocean.com/v2/droplets"
url_firewall = "https://api.digitalocean.com/v2/firewalls"


fromemail = Email("M L <devops@domain.com>")
toemail = To("6@tasks.teamwork.com")
sgapi = "SG.5"

# Predefined allowed id and IPs of droplets for firewall Hosting
firewal_hosting_name = "Hosting"
allow_drpl_hst_name = ['jump.domain.com']
allow_ip_addrses_hosting = ["11.132.0.0/16", "11.136.161.135"]

# Predefined allowed ID and IPs of droplets for firewall private-vpn-jump
firewal_jump_name = "private-vpn-jump"
allow_drpl_jump_name = ['vpn.domain.com']
allow_ip_addrses_jump = ['1.6.1.2', '1.2.1.3', ]

# Predefined allowed ID and IPs of droplets for firewall NoCloudflare
firewal_nocloudflare_name = "NoCloudflare"
allow_drpl_nocloudflare_name = ['jump.domain.com']
allow_ip_addrses_nocloudflare = []


# Send e-mail if an error
def send_email_droplet(firewall, droplets_allowed, droplets_unnecessary):
    sg = sendgrid.SendGridAPIClient(
        api_key=sgapi)
    from_email = fromemail
    to_email = toemail
    subject = f"⛔ !! Firewall named {firewall} has an unconfirmed droplet allowance"
    content = Content(
        "text/html", f"<p>Firewall <b>{firewall}</b> has an unconfirmed droplet allowance <samp>{droplets_unnecessary}</samp>.</p><p>List of allowed droplets: <samp>{droplets_allowed}</samp></p>")
    mail = Mail(from_email, to_email, subject, content)
    mail_json = mail.get()
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)


def send_email_ip(firewall, ip_allowed, ip_unnecessary):
    sg = sendgrid.SendGridAPIClient(
        api_key=sgapi)
    from_email = fromemail
    to_email = toemail
    subject = f"⛔ !! Firewall named {firewall} has an unconfirmed IPs allowance"
    content = Content(
        "text/html", f"<p>Firewall <b>{firewall}<b> has an unconfirmed IPs allowance <samp>{ip_unnecessary}</samp>.</p><p>List of allowed IPs: <samp>{ip_allowed}</samp></p>")
    mail = Mail(from_email, to_email, subject, content)
    mail_json = mail.get()
    # Send an HTTP POST request to / mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)


# Curl requests
headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"
headers["Authorization"] = f"Bearer {token}"
resp_firewall = requests.get(url_firewall, headers=headers)
firewall = resp_firewall.json()


def ged_droplet_id(list):
    for name in list:
        resp_droplets_id = requests.get(
            f"{url_droplets}?name={name}", headers=headers)
        droplets_id = resp_droplets_id.json()
        yield droplets_id['droplets'][0]['id']

allow_drpl_hst_id = list(ged_droplet_id(list=allow_drpl_hst_name))
allow_drpl_jump_id = list(ged_droplet_id(list=allow_drpl_jump_name))
allow_drpl_nocloudflare_id = list(
    ged_droplet_id(list=allow_drpl_nocloudflare_name))


# Check access by droplet ID
def get_list_drpl_ids(frwl_name, allowed_droplets):
    # Checking firewall hosting access to SSH on jump server
    for name in firewall['firewalls']:
        if name['name'] == frwl_name:
            for port in name['inbound_rules']:
                if port['ports'] == '22':
                    # get lists of droplets
                    dropletsids_present = port['sources']['droplet_ids']
                    # compare lists and find differences
                    difference_symmetric = list(
                        set(allowed_droplets).symmetric_difference(set(dropletsids_present)))
                    # get droplet names by their id
                    for ids in difference_symmetric:
                        resp_droplets = requests.get(
                            f"{url_droplets}/{ids}", headers=headers)
                        droplets_name = resp_droplets.json()
                        yield droplets_name['droplet']['name']


# Check IP access
def get_list_ip_of_drpl(frwl_name, allowed_ipadrs):
    # Checking firewall hosting access to SSH on jump server
    for name in firewall['firewalls']:
        if name['name'] == frwl_name:
            # print(frwl_name)
            for port in name['inbound_rules']:
                # print(port)
                if port['ports'] == '22':
                    # get lists of IP addresses
                    ip_present = port['sources']['addresses']
                    return list(set(ip_present).symmetric_difference(set(allowed_ipadrs)))


diff_firewall_hosting = list(get_list_drpl_ids(
    frwl_name=firewal_hosting_name, allowed_droplets=allow_drpl_hst_id))
diff_firewall_ip_hosting = list(get_list_ip_of_drpl(
    frwl_name=firewal_hosting_name, allowed_ipadrs=allow_ip_addrses_hosting))

diff_firewall_jump = list(get_list_drpl_ids(
    frwl_name=firewal_jump_name, allowed_droplets=allow_drpl_jump_id))
diff_firewall_jump_ip = get_list_ip_of_drpl(
    frwl_name=firewal_jump_name, allowed_ipadrs=allow_ip_addrses_jump)

diff_firewall_nocloudflare = list(get_list_drpl_ids(
    frwl_name=firewal_nocloudflare_name, allowed_droplets=allow_drpl_nocloudflare_id))
diff_firewall_nocloudflare_ip = get_list_ip_of_drpl(
    frwl_name=firewal_nocloudflare_name, allowed_ipadrs=allow_ip_addrses_nocloudflare)


print("diff-hosting:", diff_firewall_ip_hosting, diff_firewall_hosting)
print("diff-jump:", diff_firewall_jump_ip, diff_firewall_jump)
print("diff-nocloud:", diff_firewall_nocloudflare_ip, diff_firewall_nocloudflare)

# Send e-mail for firewall Hosting
# Droplet's ID
if diff_firewall_hosting:
    send_email_droplet(firewall=firewal_hosting_name, droplets_allowed=allow_drpl_hst_name,
                       droplets_unnecessary=diff_firewall_hosting)
else:
    print(
        f"There aren't any additional droplets that were added to the firewall {firewal_hosting_name}")
# Allowed IPs
if diff_firewall_ip_hosting:
    send_email_ip(firewall=firewal_hosting_name, ip_allowed=allow_ip_addrses_hosting,
                  ip_unnecessary=diff_firewall_ip_hosting)
else:
    print(
        f"There aren't any additional IPs that were added to the firewall {firewal_hosting_name}")


# Send e-mail for firewall Jump
# Droplet's ID
if diff_firewall_jump:
    send_email_droplet(firewall=firewal_jump_name, droplets_allowed=allow_drpl_jump_name,
                       droplets_unnecessary=diff_firewall_jump)
else:
    print(
        f"There aren't any additional droplets that were added to the firewall {firewal_jump_name}")
# Allowed IPs
if diff_firewall_jump_ip:
    send_email_ip(firewall=firewal_jump_name, ip_allowed=allow_ip_addrses_jump,
                  ip_unnecessary=diff_firewall_ip_hosting)
else:
    print(
        f"There aren't any additional IPs that were added to the firewall {firewal_hosting_name}")

# Send e-mail for firewall NoCloudflare
# Droplet's ID
if diff_firewall_nocloudflare:
    send_email_droplet(firewall=firewal_nocloudflare_name, droplets_allowed=allow_drpl_nocloudflare_name,
                       droplets_unnecessary=diff_firewall_nocloudflare)
else:
    print(
        f"There aren't any additional droplets that were added to the firewall {firewal_nocloudflare_name}")
# Allowed IPs
if diff_firewall_jump_ip:
    send_email_ip(firewall=firewal_nocloudflare_name, ip_allowed=allow_ip_addrses_nocloudflare,
                  ip_unnecessary=diff_firewall_nocloudflare_ip)
else:
    print(
        f"There aren't any additional IPs that were added to the firewall {firewal_nocloudflare_name}")
