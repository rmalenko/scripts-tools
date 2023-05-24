#!/usr/bin/env bash

# Settings
VALID_IP="1.2.3.4" # jump.domain.com

# Logins data
LOG_USER="$(whoami)"
LOG_DATE="$(date "+%Y-%m-%d %H:%M:%S")"
# OUT_WHO="$(who)"
LOG_IP="$(echo ${SSH_CLIENT} | awk '{ print $1}' )"
LOG_IP_HOST="$(host ${LOG_IP} | awk '{print substr($5, 1, length($5)-1)}')"

# SendGrid Email setup
SENDGRID_API_KEY="SG.5dr"
EMAIL_TO="6@tasks.teamwork.com"
EMAIL_SUBJECT="🦊 !! Unrecognized login on $(hostname)"
EMAIL_FROM="ML <devops@domain.com>"
EMAIL_MESSAGE="LOGIN NOTIFICATION:\n\n \
Host:     $(hostname)\n \
User:     ${LOG_USER}\n \
IP from:  ${LOG_IP} ${LOG_IP_HOST}\n \
Date:     ${LOG_DATE}\n \
          $(date)\n \
Uptime:   $(uptime)\n\n \
------------------------------------------------------------------------\n"

function email_exports()
    {
    MAIL_DATA='
        {
            "personalizations": [
                {
                    "to": [
                        {
                            "email": "'"${EMAIL_TO}"'"
                        }
                    ]
                }
            ],
            "from": {
                "email": "'"${EMAIL_FROM}"'"
            },
            "subject": "'"${EMAIL_SUBJECT}"'",
            "content": [
                {
                    "type": "text/plain",
                    "value": "'"${EMAIL_MESSAGE}"'"
                }
            ]
        }';

        curl --request POST \
            --url https://api.sendgrid.com/v3/mail/send \
            --header "authorization: Bearer ${SENDGRID_API_KEY}" \
            --header "Content-Type: application/json" \
            --data "${MAIL_DATA}"
    }




if [[ "${LOG_IP}" != "${VALID_IP}"  ]]; then
    email_exports
#else
#    echo "valid"
fi
