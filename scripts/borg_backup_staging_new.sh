#!/bin/bash

# This script creates separated backups per project, specifically volume uploads and MySQL dumps. 
# It initially sets up variables such as the location and format of the backup storage, and the number of backups to keep.
# It then sets up variables for various email settings and metrics settings, and starts the process of checking backups for consistency. 
# The script then creates and uploads a backup of each project's docker container volume and creates a MySQL database
# dump file for each project that is then uploaded to the backup server. 
# Subsequently, the script checks the last four archives for consistency and sends an email if errors are found.
# Finally, the script sends metrics into Prometheus.

BORG_SERVER_ADDR=backups.domain.com
BORG_PORT=2222
BORG_USER=borg
BORG_KEY_FILE=~/.ssh/backup.id_rsa
BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
KEEP_LAST=60
host_name="$(hostname)"
number_last_backups=4 # number of backups to check for consistency
metric_name="borg_backup_consistency"
repo_path="/mnt/backup_storage/borg/backups/"
tmp_volumes_list="/tmp/backup.lst"
node_exporter_collector_directory="/tmp/prom-metrics"

suffix="${host_name}"
date=$(date +%Y%m%d-%H%M%S)

# export BORG_REPO="ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/~/${project_name}.${suffix}"
export BORG_RSH="ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i ${BORG_KEY_FILE}"
export LANG=en_US.UTF-8
export BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
export BORG_RELOCATED_REPO_ACCESS_IS_OK=yes

# Checks if any name of a container is provided. If not, then backup all containers from the server.
if [ ${#} -eq 0 ];
then
    echo "Will backup all volumes of containers and their MySQL DBs on the ${host_name}"
    docker ps --format "{{.Names}}" | awk '/_wp/ {print substr($1, 1, length($1)-3)}' | sed '/\S/!d' > /tmp/docker.lst
elif [ ${#} -gt 1 ];
then
    echo "$0: Too many arguments: $@. Should be one container name without a suffix."
    exit 1
else
    echo "${1}: will backup all volumes and MySQL of this container -= ${1} =- on the ${host_name}"
    echo ${1} > /tmp/docker.lst
fi

# SendGrid Email setup
CheckResult() {
    HOST="${host_name}"
    SENDGRID_API_KEY="SG.5"
    EMAIL_TO="6@tasks.teamwork.com"
    EMAIL_SUBJECT="🔥 !! Backup. ${1}"
    EMAIL_FROM="ML <devops@domain.com>"
    EMAIL_MESSAGE="${1}<br><br>Details: ${2}.<br><br>Hint: ${3}"
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
                    "type": "text/html",
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

# Send metrics into the Prometheus
PublishMetrics() {
    echo "${metric_name}{job=\"borg_backup\",container=\"${2}\",zone=\"${host_name}\",host=\"${host_name}\",domain=\"${host_name}\"}${1}" >> "${node_exporter_collector_directory}/${metric_name}_${2}.prom.$$"
    if [ -f "${node_exporter_collector_directory}/${metric_name}_${2}.prom" ]; then
        rm "${node_exporter_collector_directory}/${metric_name}_${2}.prom"
    else
        echo "Metric file does not exist"
    fi
    if [ -f "${node_exporter_collector_directory}/${metric_name}_${2}.prom.$$" ]; then
        mv "${node_exporter_collector_directory}/${metric_name}_${2}.prom.$$" "${node_exporter_collector_directory}/${metric_name}_${2}.prom"
    else
        echo "Temp metric file does not exist"
    fi
}

# Create and upload a backup of docker container volume
while IFS= read -r project || [ -n "${project}" ]; do
    printf '%s\n' "${project}"
    # Creates a list of volumes in a file, excluding db.*, because Borg doesn't work if the same list of volumes is passed as variables.
    project_vol=$(realpath /var/lib/docker/volumes/"${project}"_* | grep -vE _db > "${tmp_volumes_list}")
    borg create --stats "ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/./${project}.${suffix}::${project}_volumes_${date}" $(cat "${tmp_volumes_list}") # staging
    # borg create --stats "ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/./${suffix}::${project}_volume_${date}" $(cat "${tmp_volumes_list}") # production
        if [ $? -ne 0 ]; then
            CheckResult "Failed to upload volume backup of ${project} into ${BORG_SERVER_ADDR}!" \
                "Check if path ${project}.${suffix} is present in ${BORG_SERVER_ADDR}:/mnt/backup_storage/borg/backups/${project}.${suffix}" \
                "Run sudo -u backups borg init -e none ${project}.${suffix} on ${BORG_SERVER_ADDR}"
        fi
done < /tmp/docker.lst

# Create mysql database dump file and upload to Borg server
    # --single-transaction says "For transactional tables such as InnoDB no changes that occur to InnoDB tables during the dump will be included in the dump". So, effectively, the dump is a snapshot of the databases at the instant the dump started, regardless of how long the dump takes.
    # --skip-lock-tables parameter instructs the mysqldump utility not to issue a LOCK TABLES command before obtaining the dump which will acquire a READ lock on every table. All tables in the database should be locked, for improved consistency in case of a backup procedure. Even with skip-lock-tables, while a table is dumped, will not receive any INSERTs or UPDATEs whatsoever, as it will be locked due the SELECT required to obtain all records from the table. It looks like this 
    # --extended-insert Write INSERT statements using multiple-row syntax that includes several VALUES lists. This results in a smaller dump file and speeds up inserts when the file is reloaded. 
    # If you are using a recent version of mysqldump to generate a dump to be reloaded into a very old MySQL server, use the --skip-opt option instead of the --opt or --extended-insert option. 
    # --routines Dump stored routines (procedures and functions) from dumped databases
    # --events, Include Event Scheduler events for the dumped databases in the output. This option requires the EVENT privileges for those databases. 
    # --no-tablespaces This option suppresses all CREATE LOGFILE GROUP and CREATE TABLESPACE statements in the output of mysqldump. 

while IFS= read -r project || [ -n "${project}" ]; do
    printf '%s\n' "${project}"
    docker exec "${project}"_mysql env | grep MYSQL_ > /opt/backups/.env
    source /opt/backups/.env
    docker exec "${project}"_mysql /usr/bin/mysqldump --single-transaction --skip-lock-tables --extended-insert --max_allowed_packet=512M --routines --events --no-tablespaces \
        -u root --password=${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} | gzip > /srv/${project}_mysql_${date}.sql.gz || \
        CheckResult "Failed dumping database of ${project}." "An error happened while backing was created on the server ${host_name}"
    borg create --stats "ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/./${project}.${suffix}::${project}_mysql_${date}" "/srv/${project}_mysql_${date}.sql.gz" \
        || {
                CheckResult "Failed upload dump of database ${project} from server ${host_name}." \
                    "Check if path is present ${project}.${suffix} in ${BORG_SERVER_ADDR}:/mnt/backup_storage/borg/backups/${project}.${suffix}" \
                    "Run sudo -u backups borg init -e none ${project}.${suffix} on ${BORG_SERVER_ADDR}."
            }
    find /srv -maxdepth 1 -type f -name "*.sql.gz" -delete
done < /tmp/docker.lst

# Check the last four atchives for consistency
while IFS= read -r project || [ -n "${project}" ]; do
    printf '%s\n' "${project}"
    echo "---------------------"
    borg check -v --archives-only --save-space --first ${number_last_backups} "ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/./${project}.${suffix}"
    exitcode=${?}
    PublishMetrics ${exitcode} ${project}
    if [ $exitcode -ne 0 ]; then
        CheckResult "Consistency checking of ${project} on the server ${host_name} does not pass. One of the last four archives may contain an error." \
            "Check if path is present ${project}.${suffix} in ${BORG_SERVER_ADDR}:/mnt/backup_storage/borg/backups" \
            "borg list --last 4 '{archive}{NL}' /mnt/backup_storage/borg/backups/${project}.${suffix}"
    else
        echo "Successfully in ${project}, exit code: ${exitcode}"
    fi
done < /tmp/docker.lst


# Ensures retention policy of the backups from this particular machine
while IFS= read -r project || [ -n "${project}" ]; do
    printf '%s\n' "${project}_volumes_* ${project}_mysql_*"
    echo "---------------------"
    borg prune -v --list --stats --keep-yearly=1 --keep-weekly=20 --keep-daily=30 --glob-archives=\'"${project}_volumes_*"\' "ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/./${project}.${suffix}" \
        || {
                CheckResult "Prune error of ${project}_volume_* backup of ${host_name}." 
            }
    borg prune -v --list --stats --keep-yearly=1 --keep-weekly=20 --keep-daily=30 --glob-archives=\'"${project}_mysql_*"\' "ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/./${project}.${suffix}" \
        || {
                CheckResult "Prune error of ${project}_mysql_* backup of ${host_name}." 
            }
done < /tmp/docker.lst
