#! /bin/bash
USERNAME="magicUser"
PASSWD="uberPasswd"

wget -qO- --keep-session-cookies --save-cookies cookies.txt --no-check-certificate \
https://192.168.1.1/status_dhcp_leases.php | grep "name='__csrf_magic'" \
| sed 's/.*value="\(.*\)".*/\1/' > csrf.txt

wget -qO- --keep-session-cookies --load-cookies cookies.txt --save-cookies cookies.txt \
--no-check-certificate \
--post-data "login=Login&usernamefld=$USERNAME&passwordfld=$PASSWD&__csrf_magic=$(cat csrf.txt)" \
https://192.168.1.1/status_dhcp_leases.php  | grep "name='__csrf_magic'" \
| sed 's/.*value="\(.*\)".*/\1/' > csrf2.txt

wget --keep-session-cookies --load-cookies cookies.txt --no-check-certificate \
https://192.168.1.1/status_dhcp_leases.php

rm cookies.txt csrf2.txt csrf.txt
