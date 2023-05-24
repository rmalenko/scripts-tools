#!/bin/bash

echo -n "Enter DO API key:" 
read api_key

do_api_key="${api_key}"
droplets=`(doctl -t "${do_api_key}" compute droplet list --output json | jq .[].id)`
tag="monitoring_yes"

while IFS= read -r line
do
   doctl -t "${do_api_key}" compute droplet tag "${line}" --tag-name="${tag}"
   echo "The tag: ${tag} has been added to Droplet ${line}"
done < <(printf '%s\n' "${droplets}")