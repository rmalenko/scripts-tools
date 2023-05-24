#!/bin/bash

# The script will restore only volume of uploads folder or MySQL DB or both from staging backups to staging.

server="${1}"
project="${2}"
backup_type="${3}"
backup_date="${4}"
# We got the number of days and then used the value in the last N archives.
# Because we have daily backups, we have sorted by date list of archives in ascending order (oldest/earliest dates).
# We need to sort in descending order to get an archive for one day ago. Then the first line is a day ago, the second line two days ago, etc...

volume_restore="var/lib/docker/volumes/${project}_uploads"

BORG_SERVER_ADDR=backups.domain.com
BORG_PORT=2222
BORG_USER=borg
BORG_KEY_FILE=~/.ssh/backup.id_rsa
BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
host_name="$(hostname)"
suffix="${host_name}"
borg_server="ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/./${project}.dsstaging${server}.com"

export BORG_REPO="ssh://${BORG_USER}@${BORG_SERVER_ADDR}:${BORG_PORT}/~/${project_name}.${suffix}"
export BORG_RSH="ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i ${BORG_KEY_FILE}"
export LANG=en_US.UTF-8
export BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
export BORG_RELOCATED_REPO_ACCESS_IS_OK=yes

usage() {
    echo "Usage: $0 <1> <project_name> <uploads or mysql or full> <number days ago>"
    exit 1
}

if [ -z ${server} ]; then
    echo "-= A number of staging server is missing =-"
    echo "____________________________"
    usage
elif [ -z ${project} ]; then
    echo "-= A project name server is missing =-"
    echo "____________________________"
    usage
elif [ -z ${backup_type} ]; then
    echo "-= A type of backup didn't provide (uploads, mysql or full) =-"
    echo "____________________________"
    usage
elif [[ "${backup_type}" != "uploads" && "${backup_type}" != "mysql" && "${backup_type}" != "full" ]]; then
    echo "Error: Backup type must be 'uploads' or 'mysql' or 'full'"
    echo "____________________________"
    usage
elif [ -z ${backup_date} ]; then
    echo "A number day of backup didn't provide"
    echo "____________________________"
    usage
elif [[ ! "${backup_date}" =~ ^[0-9]+$ ]]; then
    echo "Error: checks if the backup date is a number"
    echo "____________________________"
    usage
else
    echo "Restoring project ${2} backup of ${3} for date ${4} on host: ${host_name}"
fi

volumes_restore() {
    volumes_to_restore="$(borg list --glob-archives='*volume*' --sort-by timestamp --last ${backup_date} --short ${borg_server} | sort -r | awk NR==${backup_date})"
    echo "-= Extracting all volumes folders and files from volume backup from ${backup_date} days ago =-"
    echo "____________________________"
    mkdir -p /tmp/volumes
    cd /tmp/volumes
    # borg extract "${borg_server}::${volumes_to_restore}"
    borg extract "${borg_server}::${volumes_to_restore}" "${volume_restore}"
    cd /tmp/volumes/var/lib/docker/volumes
    rsync -av -R . /var/lib/docker/volumes
    rm -r /tmp/volumes/*
}

mysql_restore() {
    mysql_to_restore="$(borg list --glob-archives='*mysql*' --sort-by timestamp --last ${backup_date} --short ${borg_server} | sort -r | awk NR==${backup_date})"
    echo "-= Restore MySQL from ${backup_date} days ago =-"
    echo "____________________________"
    mkdir -p /tmp/sql
    cd /tmp/sql
    borg extract "${borg_server}::${mysql_to_restore}"
    cd /tmp/sql/srv
    gunzip "${mysql_to_restore}.sql.gz"
    docker exec "${project}"_mysql env | grep MYSQL_ > ./.env.mysql
    source ./.env.mysql
    cat "./${mysql_to_restore}.sql" | docker exec -i "${project}"_mysql /usr/bin/mysql -u root --password=${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE}
    rm -r /tmp/sql/*
}

if [[ "${backup_type}" == "uploads" ]]; then
    volumes_restore
elif [[ "${backup_type}" == "mysql" ]]; then
    mysql_restore
elif [[ "${backup_type}" == "full" ]]; then
    volumes_restore
    mysql_restore
else
    echo "-= A backup type isn't provided =-"
fi
