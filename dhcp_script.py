#!/usr/bin/env python2
# -*- coding: <UTF-8> -*-
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE

comm = Popen("./getDHCPlease.sh", shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
stdout, stderr = comm.communicate()

count = 0
soup = BeautifulSoup(open('status_dhcp_leases.php','r').read(), "lxml")
table = soup.find('table', attrs={'class':'table'})
body = table.findAll("tbody")
tr = []
for group in body:
    tr += group.findAll("tr")
td = []
for group in tr:
    td += group.findAll("td")
for i in td:
    if 'online' in i:
        count += 1
prevUs = open('lastHack.txt','r')
prevUs_data = prevUs.read()
prevUs.close()
if prevUs_data != str(count):
    finalComm = "./sendUsers.sh " + str(count)
    comm = Popen(finalComm, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = comm.communicate()
    prevUs = open('lastHack.txt','w+')
    prevUs.write(str(count))
comm = Popen("rm status_dhcp_leases.php", shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
stdout, stderr = comm.communicate()
