#!/bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
DATE=$(date +"%F-%H")
docker exec macs-verify-db mongodump --archive=/dump.mdb && docker cp macs-verify-db:/dump.mdb /home/docker/discord-verify/backups/$DATE.mdb
