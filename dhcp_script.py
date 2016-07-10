#!/usr/bin/env python2
# -*- coding: <UTF-8> -*-
"""In a space with a pfSense Router, get #of active devices and misc. stats."""
import ssl
import os
#import urllib2
import cookielib
from subprocess import Popen, PIPE
from bs4 import BeautifulSoup
import yaml
import mechanize


DEBUG = False


def get_lease_file(current_dir, pfSenseKeySet, pfSenseCfg):
    """Login to pfSense, get DHCP Leases page and save it to a file."""
    cj = cookielib.CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.set_handle_robots(False)
    #Don't verify pfSense's cert signing authority
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context
    br.open(pfSenseCfg['url'])
    br.select_form(nr=0)
    br.form['usernamefld'] = pfSenseKeySet['user']
    br.form['passwordfld'] = pfSenseKeySet['pass']
    br.submit()
    htmlFilePath = current_dir + "/status_dhcp_leases.php"
    with open(htmlFilePath, 'w') as htmlFile:
        htmlFile.write(br.response().read())
    return 0


def parse_html(current_dir):
    """Parse DHCP Leases page, return hosts by MAC and their state."""
    final = []
    htmlFilePath = current_dir + "/status_dhcp_leases.php"
    with open(htmlFilePath, 'r') as lease_html:
        soup = BeautifulSoup(lease_html.read(), "lxml")
    #Get and parse the <table> element
    table = soup.find('table', attrs={'class':'table'})
    soupT = BeautifulSoup(str(table), "lxml")
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


def m_pub(current_dir, mosquittoKeySet, mqttCfg, topicPath, data):
    """Publish at mqtt Instance"""
    command = "mosquitto_pub -h "
    command += mqttCfg['host']
    command += " -u "
    command += mosquittoKeySet['user']
    command += " -P "
    command += mosquittoKeySet['pass']
    command += " --cafile "
    command += current_dir
    command += mqttCfg['cafile']
    command += " -t \""
    command += topicPath
    command += "\" -m \""
    command += data
    command += "\""
    if DEBUG:
        print command
    comm = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = comm.communicate()
    return 0


def send_users(current_dir, mqttKeySet, mqttCfg, noUsers):
    """Construct /hackers subtopic & publish."""
    topic = mqttCfg['topicRoot'] + "/hackers"
    m_pub(current_dir, mqttKeySet, mqttCfg, topic, str(noUsers))
    return 0


def send_new_macs(current_dir, mqttKeySet, mqttCfg, newMACs):
    """Construct /stats topic & publish."""
    topic = mqttCfg['topicRoot'] + "/stats"
    data = str(len(newMACs))
    m_pub(current_dir, mqttKeySet, mqttCfg, topic, data)
    return 0


def handle_new_macs(current_dir, mqttKeySet, mqttCfg, newMACs):
    """Add new MACs to the yml file & publish"""
    macFilePath = current_dir + "/uniqueMAC.yml"
    with open(macFilePath, 'a') as mac_file:
        for macAddress in newMACs:
            macStr = "\n  - " + macAddress
            mac_file.write(macStr)
    send_new_macs(current_dir, mqttKeySet, mqttCfg, newMACs)
    return 0


def handle_users(current_dir, mqttKeySet, mqttCfg, count):
    """Check if #of users has changed & publish"""
    lastHackPath = current_dir + "/lastHack.txt"
    try:
        prevUs = open(lastHackPath, 'r')
    except IOError:
        prevUs_data = ""
    else:
        prevUs_data = prevUs.read()
        prevUs.close()
    if prevUs_data != str(count):
        send_users(current_dir, mqttKeySet, mqttCfg, count)
        prevUs = open(lastHackPath, 'w')
        prevUs.write(str(count))


def main():
    """Read configuration, pass around variables."""
    count = 0
    newMACs = []
    #Read config file and get neutral MAC Addresses, keySets and current_dir
    ymlPath = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
    with open(ymlPath, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    staticMAC = cfg['macAddresses']
    pfSenseKeySet = cfg['pfSense']
    pfSenseCfg = cfg['pfSenseCfg']
    mosquittoKeySet = cfg['mosquitto']
    mqttCfg = cfg['mqttCfg']
    current_dir = cfg['userspace']['cwd']
    #Read unique MACs that have been on the network (for statistics)
    uniqueMACPath = current_dir + "/uniqueMAC.yml"
    with open(uniqueMACPath, 'r') as uniqueMACFile:
        mac_file = yaml.load(uniqueMACFile)
    uniqueMACs = mac_file['uniqueMAC']
    if uniqueMACs is None:
        uniqueMACs = []
    #Run script to get the HTML containing the DHCP leases
    get_lease_file(current_dir, pfSenseKeySet, pfSenseCfg)
    #Parse HTML
    active_hosts = parse_html(current_dir)
    for dataSet in active_hosts:
        #If device is online and not one of the neutral device count one
        if dataSet[1] == 'online' and dataSet[0] not in staticMAC:
            count += 1
            if dataSet[0] not in uniqueMACs:
                newMACs.append(dataSet[0])
    if newMACs:
        handle_new_macs(current_dir, mosquittoKeySet, mqttCfg, newMACs)
    handle_users(current_dir, mosquittoKeySet, mqttCfg, count)
    #Final clean-up
    command = "rm " + current_dir + "/status_dhcp_leases.php"
    comm = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = comm.communicate()


if __name__ == '__main__':
    main()
