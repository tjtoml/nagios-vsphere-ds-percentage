[![Pylint](https://github.com/tjtoml/nagios-vsphere-ds-percentage/actions/workflows/pylint.yml/badge.svg?event=push)](https://github.com/tjtoml/nagios-vsphere-ds-percentage/actions/workflows/pylint.yml)
# nagios-vsphere-ds-percentage

## Description:
A check plugin for [nagios](https://www.nagios.org) that will check the percentage used of a vSphere datastore. Written in `python3`, utilizes [`govc`](https://github.com/vmware/govmomi/tree/main/govc) to communicate with vSphere. I wrote this because the vSphere plugin that came with Nagios XI did not fit my company's requirements for a simple check to see if a vSphere datastore's usage exceeded a certain threshold.  

```shell 
usage: vsphere_ds_percentage.py [-h] [-H HOST] [-u USERNAME] [-p PASSWORD] [-k] [-f FILE] [-w WARN] [-c CRIT]
                                [-d DATASTORE]

Nagios check script for the percentage used of a vSphere datastore

options:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  The vSphere host | GOVC_URL (string)
  -u USERNAME, --username USERNAME
                        The user to connect as | GOVC_USERNAME (string)
  -p PASSWORD, --password PASSWORD
                        The user's password | GOVC_PASSWORD (string)
  -k, --insecure        Don't verify SSL certificates for the vSphere host | GOVC_INSECURE (boolean)
  -f FILE, --file FILE  A yaml-formatted config file
  -w WARN, --warn WARN, --warning WARN
                        The percentage at which at a datastore will be in a WARNING state
  -c CRIT, --crit CRIT, --critical CRIT
                        The percentage at which a datastore will be in a CRITICAL state
  -d DATASTORE, --datastore DATASTORE
                        The name of the datastore to check
```
## Installation:

Requires Python 3.   


Requires [`govc`](https://github.com/vmware/govmomi/tree/main/govc) available on the `$PATH` for the user running the `nagios` process. 

See [`requirements.txt`](requirements.txt) for Python dependencies. I recommend using your system package manager to install `pyyaml`, which is the only current dependency:  
```shell
dnf install python3-pyyaml #Red Hat variants
apt install python3-yaml #Debian variants
```
etc.

## Usage

Should work like any other `nagios` check plugin.  

You can pass configuration directly as arguments, by using a config file ([example](config.yaml.example)), by setting the relevant `GOVC_` environment variables for your `nagios` user, or any combination of these. If a configuration option is set in multiple ways, an argument will override a config file directive, which will override an environment variable.

## Examples:

#### Check a single datastore, WARN at 75% used and CRIT at 90%, do not check vSphere SSL certificate for validity:
```shell
vsphere_ds_percentage.py -d SINGLE_DATASTORE -w 75 -c 90 -k --username="someUser@vsphere.local" \
password="thisIs@passw0rd" --host="vsphere.local"
VSPHERE_DATASTORE OK: SINGLE_DATASTORE Used: 43.9%
echo $?
0 #OK
```
#### Check a single datastore, WARN at 75% used and CRIT at 90%, check vSphere SSL certificate for validity, using config file:

```shell
cat /home/someuser/config.yml
---
GOVC_URL: vsphere.local
GOVC_USERNAME: someUser@vsphere.local
GOVC_PASSWORD: thisIs@passw0rd
GOVC_INSECURE: 0

vsphere_ds_percentage.py -d OTHER_DATASTORE -w 75 -c 90 -f /home/someuser/config.yml
VSPHERE_DATASTORE WARNING: SINGLE_DATASTORE Used: 76.9%
echo $?
1 #WARNING
```

#### Check all datastores, WARN at 75% used and CRIT at 90%, using config file
```shell
vsphere_ds_percentage.py -w 75 -c 90 -f /home/someuser/config.yml
VSPHERE_DATASTORE CRITICAL: CRITICAL-DATASTORE Used: 93.1%
VSPHERE_DATASTORE OK: OK-DATASTORE-1 Used: 52.8%
VSPHERE_DATASTORE OK: OK-DATASTORE-2 Used: 72.4%
VSPHERE_DATASTORE OK: OK-DATASTORE-3 Used: 43.9%
VSPHERE_DATASTORE OK: OK-DATASTORE-4 Used: 47.8%
VSPHERE_DATASTORE WARNING: WARNING-DATASTORE Used: 83.3%
VSPHERE_DATASTORE OK: OK-DATASTORE-5 Used: 64.2%
echo $?
2 #CRITICAL
``` 
NOTE: Checking all datastores will return the highest status. In the example above, there is one CRITICAL datastore, but the entire nagios service will be critical.

## Contributing

Pull requests welcomed! 
