#! /bin/bash

noUsers=$1
currentDirectory=$(pwd)
mosquitto_pub -h www.techministry.gr -u magicUsername -P uberPasswd --cafile $currentDirectory/MQTT-CA-TM.crt  -t "techministry/spacestatus/hackers" -m "$noUsers"
