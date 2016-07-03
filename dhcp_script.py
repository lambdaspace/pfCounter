#!/usr/bin/env python2
# -*- coding: <UTF-8> -*-
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE
import yaml
import mechanize
import urllib2
import cookielib
import ssl
import os


def getLeaseFile(currentDirectory, pfSenseKeySet):
    cj = cookielib.CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.set_handle_robots(False)
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context
    br.open("https://pfSense.techministry.gr")
    br.select_form(nr=0)
    br.form['usernamefld'] = pfSenseKeySet['user']
    br.form['passwordfld'] = pfSenseKeySet['pass']
    br.submit()
    htmlFilePath = currentDirectory + "/status_dhcp_leases.php"
    with open(htmlFilePath,'w') as htmlFile:
        htmlFile.write(br.response().read())
    return 0


def parseHTML(currentDirectory):
    final = []
    htmlFilePath = currentDirectory + "/status_dhcp_leases.php"
    with open(htmlFilePath,'r') as lease_html:
        soup = BeautifulSoup(lease_html.read(), "lxml")
    #Get and parse the <table> element
    table = soup.find('table', attrs={'class':'table'})
    soupT = BeautifulSoup(str(table),"lxml")
    body = soupT.find('tbody')
    bodys = body.findAll('tr')
    for i in range(len(bodys)):
        tmp = []
        #Get each line of the DHCP lease table body
        bodys[i] = bodys[i].findAll('td')
        #Add the 3d and 8th element of each line as an array (MAC & online status)
        tmp.append(str(bodys[i][2].getText()).translate(None, '\n\t'))
        tmp.append(str(bodys[i][7].getText()).translate(None, '\n\t'))
        final.append(tmp)
    return final


def mPublish(currentDirectory, mosquittoKeySet, topicPath, data):
    command = "mosquitto_pub -h www.techministry.gr -u "
    command += mosquittoKeySet['user']
    command += " -P "
    command += mosquittoKeySet['pass']
    command += " --cafile "
    command += currentDirectory
    command += "/MQTT-CA-TM.crt  -t \""
    command += topicPath
    command += "\" -m \""
    command += data
    command += "\""
    comm = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = comm.communicate()
    return 0


def sendUsers(currentDirectory, mosquittoKeySet, noUsers):
    topic = "techministry/spacestatus/hackers"
    mPublish(currentDirectory, mosquittoKeySet, topic, str(noUsers))
    return 0


def sendNewMACs(currentDirectory, mosquittoKeySet, newMACs):
    topic = "techministry/spacestatus/stats"
    data = str(len(newMACs))
    mPublish(currentDirectory, mosquittoKeySet, topic, data)
    return 0


def handleNewMACs(currentDirectory, mosquittoKeySet, newMACs):
    macFilePath = currentDirectory + "/uniqueMAC.yml"
    with open(macFilePath,'a') as mac_file:
        for macAddress in newMACs:
            macStr = "\n  - " + macAddress
            mac_file.write(macStr)
    sendNewMACs(currentDirectory, mosquittoKeySet, newMACs)
    return 0


def handleUsers(currentDirectory, mosquittoKeySet, count):
    #Check if users have changed
    lastHackPath = currentDirectory + "/lastHack.txt"
    try:
        prevUs = open(lastHackPath,'r')
    except IOError:
        prevUs_data = ""
    else:
        prevUs_data = prevUs.read()
        prevUs.close()
    if prevUs_data != str(count):
        sendUsers(currentDirectory, mosquittoKeySet, count)
        prevUs = open(lastHackPath,'w')
        prevUs.write(str(count))


def main():
    count = 0
    newMACs = []
    #Read config file and get neutral MAC Addresses, keySets and currentDirectory
    ymlPath = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
    with open(ymlPath,'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    staticMAC = cfg['macAddresses']
    pfSenseKeySet = cfg['pfSense']
    mosquittoKeySet = cfg['mosquitto']
    currentDirectory = cfg['userspace']['cwd']
    #Read unique MACs that have been on the network (for statistics)
    uniqueMACPath = currentDirectory + "/uniqueMAC.yml"
    with open(uniqueMACPath,'r') as uniqueMACFile:
        mac_file = yaml.load(uniqueMACFile)
    uniqueMACs = mac_file['uniqueMAC']
    if uniqueMACs is None:
        uniqueMACs = []
    #Run script to get the HTML containing the DHCP leases
    getLeaseFile(currentDirectory, pfSenseKeySet)
    #Parse HTML
    active_hosts = parseHTML(currentDirectory)
    for dataSet in active_hosts:
        #If device is online and not one of the neutral device count one
        if dataSet[1]=='online' and dataSet[0] not in staticMAC:
                count += 1
                if dataSet[0] not in uniqueMACs:
                    newMACs.append(dataSet[0])
    if newMACs:
        handleNewMACs(currentDirectory, mosquittoKeySet, newMACs)
    handleUsers(currentDirectory, mosquittoKeySet, count)
    #Final clean-up
    command = "rm " + currentDirectory + "/status_dhcp_leases.php"
    comm = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = comm.communicate()


if __name__ == '__main__':
    main()
