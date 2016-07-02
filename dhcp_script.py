#!/usr/bin/env python2
# -*- coding: <UTF-8> -*-
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE
import yaml

#Read config file and get neutral MAC Addresses
with open("config.yml",'r') as ymlfile:
    cfg = yaml.load(ymlfile)
staticMAC = cfg['macAddresses']

#Run script to get the HTML containing the DHCP leases
comm = Popen("./getDHCPlease.sh", shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
stdout, stderr = comm.communicate()

count = 0
#Parse HTML
soup = BeautifulSoup(open('status_dhcp_leases.php','r').read(), "lxml")
#Get and parse the <table> element
table = soup.find('table', attrs={'class':'table'})
soupT = BeautifulSoup(str(table),"lxml")
body = soupT.find('tbody')
bodys = body.findAll('tr')
final = []
for i in range(len(bodys)):
    tmp = []
    #Get each line of the DHCP lease table body
    bodys[i] = bodys[i].findAll('td')
    #Add the 3d and 8th element of each line as an array (MAC & online status)
    tmp.append(str(bodys[i][2].getText()).translate(None, '\n\t'))
    tmp.append(str(bodys[i][7].getText()).translate(None, '\n\t'))
    final.append(tmp)
for dataSet in final:
    #If device is online and not one of the neutral device count one
    if dataSet[1]=='online' and dataSet[0] not in staticMAC:
        count += 1
#Check if users have changed
prevUs = open('lastHack.txt','r')
prevUs_data = prevUs.read()
prevUs.close()
if prevUs_data != str(count):
    #Call sendUsers.sh followed by the number of users
    finalComm = "./sendUsers.sh " + str(count)
    comm = Popen(finalComm, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = comm.communicate()
    #Write the new number
    prevUs = open('lastHack.txt','w+')
    prevUs.write(str(count))
#Final clean-up
comm = Popen("rm status_dhcp_leases.php", shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
stdout, stderr = comm.communicate()
