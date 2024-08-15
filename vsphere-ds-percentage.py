#!/usr/bin/env python3
import json
import subprocess
import sys
import os
import argparse
import yaml

def validate_config(args, config):
    if args.host:
        host = args.host
    elif "GOVC_URL" in config:
        host = config['GOVC_URL']
    elif os.environ.get('GOVC_URL'):
        host = os.environ.get('GOVC_URL')
    else:
        print("No vSphere host set - check config!")
        sys.exit(3)

    if args.username:
        username = args.username
    elif "GOVC_USERNAME" in config:
        username = config['GOVC_USERNAME']
    elif os.environ.get('GOVC_USERNAME'):
        username = os.environ.get('GOVC_USERNAME')
    else:
        print("No vSphere username set - check config!")
        sys.exit(3)

    if args.password:
        password = args.password
    elif "GOVC_PASSWORD" in config:
        password = config['GOVC_PASSWORD']
    elif os.environ.get('GOVC_PASSWORD'):
        password = os.environ.get('GOVC_PASSWORD')
    else:
        print("No vSphere password set - check config!")
        sys.exit(3)

    if args.insecure is False:
        if "GOVC_INSECURE" in config:
            insecure = bool(config['GOVC_INSECURE'])
        elif os.environ.get('GOVC_INSECURE'):
            insecure = bool(eval(os.environ.get('GOVC_INSECURE')))
    else:
        insecure = args.insecure

    valid_config = {"host": host, "username": username, "password": password,
                    "insecure": insecure}

    return valid_config

def get_datastore_info(dsinfo, datastore, warn_percent, crit_percent):
    status_code = 3
    status_text = "UNKNOWN: Datastore " + datastore + " Not Found"
    used_percent = None

    for ds in dsinfo['datastores']:
        if ds['name'] == datastore:
            free_space = ds['summary']['freeSpace']
            capacity = ds['summary']['capacity']
            used_percent = round((1 - (free_space / capacity)) * 100, 1)

            if used_percent >= crit_percent:
                status_text = "CRITICAL: " + datastore
                status_code = 2
            elif used_percent >= warn_percent:
                status_text = "WARNING: " + datastore
                status_code = 1
            else:
                status_text = "OK: " + datastore
                status_code = 0

    status = {"status_text": status_text, "status_code": status_code,
              "used_percent": used_percent}
    return status

def parse_arguments():
    parser = argparse.ArgumentParser(
            prog='vsphere-ds-percentage.py',
            description='Nagios check script for the percentage used of a vSphere datastore')

    parser.add_argument('-H', '--host',
                        help='The vSphere host | GOVC_URL (string)')
    parser.add_argument('-u', '--username',
                        help='The user to connect as | GOVC_USERNAME (string)')
    parser.add_argument('-p', '--password',
                        help='The user\'s password | GOVC_PASSWORD (string)')
    parser.add_argument('-k', '--insecure',
                        action='store_true',
                        default=False,
                        help='Don\'t verify SSL certificates for the vSphere host | GOVC_INSECURE (boolean)')
    parser.add_argument('-f', '--file',
                        help='A yaml-formatted config file')
    parser.add_argument('-w', '--warn', '--warning',
                        help='The percentage at which at a datastore will be in a WARNING state',
                        type=int)
    parser.add_argument('-c', '--crit', '--critical',
                        help='The percentage at which a datastore will be in a CRITICAL state',
                        type=int)
    parser.add_argument('datastore',
                        help='The name of the datastore to check')

    args = parser.parse_args()
    return args

args = parse_arguments()

if args.file:
    try:
        config = yaml.safe_load(open(args.file))
    except Exception:
        config = {}
        pass
else:
    config = {}

valid_config = validate_config(args, config)

datastore = args.datastore

warn_percent = args.warn
crit_percent = args.crit

command = "govc datastore.info -json"

os.environ['GOVC_URL'] = valid_config['host']
os.environ['GOVC_USERNAME'] = valid_config['username']
os.environ['GOVC_PASSWORD'] = valid_config['password']
os.environ['GOVC_INSECURE'] = str(valid_config['insecure'])

try:
    output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as exc:
    print("VSPHERE_DATASTORE UNKNOWN: ", exc.output, end='', sep='')
    sys.exit(status_code)

dsinfo = json.loads(output)

output = get_datastore_info(dsinfo, datastore, warn_percent, crit_percent)
if output["used_percent"] is not None:
    print("VSPHERE_DATASTORE ", output['status_text'],  " Used: ",
          output["used_percent"], "%", sep='')
    sys.exit(output['status_code'])
else:
    print("VSPHERE_DATASTORE ", output['status_text'], sep='')
    sys.exit(output['status_code'])
