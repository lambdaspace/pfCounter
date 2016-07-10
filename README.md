# pfCounter

![MIT Licence](https://img.shields.io/badge/Licence-MIT_Licence-red.svg?style=plastic)
[![Python 2.7](https://img.shields.io/badge/Python-2.7-yellow.svg?style=plastic)](https://www.python.org/)
![Maintained](https://img.shields.io/badge/Maintained-Yes-green.svg?style=plastic)

> A script that gets connected devices in a network, from a pfSense Router.

## Required

* A pfSense Router
* A linux machine that will run 24/7 (a pi maybe?)
* Mosquitto client installed on said machine (v1.4.9)
* Python 2.7 installed on said machine
* pip installed on said machine
* An mqtt Broker (v3.1)

## Deployment

* Clone this repo on your linux machie
* Create a new user on your pfSense Router and only assign "WebCfg - Status: DHCP leases" to it
* On your Linux machine navigate to the project forlder and give `pip install -r requirements.txt`
* Rename config.yml.dist to config.yml
* Edit config.yml
  * userspace
    * cwd : the root folder the script resides into (no trailing '/')
  * macAddresses : A list of the MAC addresses of the devices that should not be accounted for
  * pfSense
    * user : username for the user you created on pfSense
    * pass : password for said user
  * pfSenseCfg
    * url : the url pfSense is at
  * mosquitto
    * user : username for the user that will publish at the MQTT Broker
    * pass : said user's password
  * mqttCfg
    * host : the server the MQTT broker is located at
    * topicRoot : the root of the topics the script should publish at (no trailing '/')
    * cafile : the name/directory of the crt file of the CA that signed the MQTT Broker's cert
* Add a cron job on your Linux machine to periodicly run the script 
* If you want to get data more frequently than 20 minutes you will have to change net.link.ether.inet.max_age at pfSense
  * to do so go to System > Advanced > System Tunables and add a new tunable with the 'net.link.ether.inet.max_age' and as a value the number of seconds (something a bit smaller than the sampling frequency)

