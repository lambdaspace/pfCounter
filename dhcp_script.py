#!/usr/bin/env python2
# -*- coding: <UTF-8> -*-
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE

staticMAC = []

comm = Popen("./getDHCPlease.sh", shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
stdout, stderr = comm.communicate()

count = 0
soup = BeautifulSoup(open('status_dhcp_leases.php','r').read(), "lxml")
table = soup.find('table', attrs={'class':'table'})
soupT = BeautifulSoup(str(table),"lxml")
head = soupT.find('thead')
body = soupT.find('tbody')
headers = head.findAll('th')
bodys = body.findAll('tr')
final = []
for i in range(len(bodys)):
    tmp = []
    bodys[i] = bodys[i].findAll('td')
    tmp.append(str(bodys[i][2].getText()).translate(None, '\n\t'))
    tmp.append(str(bodys[i][7].getText()).translate(None, '\n\t'))
    final.append(tmp)
for dataSet in final:
    if dataSet[1]=='online' and dataSet[0] not in staticMAC:
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
