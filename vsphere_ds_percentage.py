#!/usr/bin/env python3
"""Nagios Check for a vSphere datastore, by percentage used. """
import json
import subprocess
import sys
import os
import argparse
from ast import literal_eval
import yaml

def validate_host(args, config):
    """Validates user input for vSphere host"""
    if args.host:
        host = args.host
    elif "GOVC_URL" in config:
        host = config['GOVC_URL']
    elif os.environ.get('GOVC_URL'):
        host = os.environ.get('GOVC_URL')
    else:
        print("No vSphere host set - check config!")
        sys.exit(3)
    return host

def validate_username(args, config):
    """ Validates user input for vSphere username """
    if args.username:
        username = args.username
    elif "GOVC_USERNAME" in config:
        username = config['GOVC_USERNAME']
    elif os.environ.get('GOVC_USERNAME'):
        username = os.environ.get('GOVC_USERNAME')
    else:
        print("No vSphere username set - check config!")
        sys.exit(3)
    return username

def validate_password(args, config):
    """ Validates user input for vSphere password"""
    if args.password:
        password = args.password
    elif "GOVC_PASSWORD" in config:
        password = config['GOVC_PASSWORD']
    elif os.environ.get('GOVC_PASSWORD'):
        password = os.environ.get('GOVC_PASSWORD')
    else:
        print("No vSphere password set - check config!")
        sys.exit(3)
    return password

def validate_config(args, config):
    """
    Takes user input and validates the config. Config precedence flag>config
    file>environment variable.
    """
    valid_host = validate_host(args, config)
    valid_username = validate_username(args, config)
    valid_password = validate_password(args, config)

    insecure = False
    if args.insecure is False:
        if "GOVC_INSECURE" in config:
            insecure = bool(config['GOVC_INSECURE'])
        elif os.environ.get('GOVC_INSECURE'):
            insecure = bool(literal_eval(os.environ.get('GOVC_INSECURE')))
    else:
        insecure = args.insecure

    valid_config = {"host": valid_host, "username": valid_username, "password":
                    valid_password,
                    "insecure": insecure}

    return valid_config

def get_datastore_info(dsinfo, datastore, warn_percent, crit_percent):
    """ Gets the used percentage for a selected datastore from govc json output
    """
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
    """Parses the arguments passed to the script """
    parser = argparse.ArgumentParser(
            prog='vsphere_ds_percentage.py',
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
                        help="""Don\'t verify SSL certificates for the vSphere host | GOVC_INSECURE
                        (boolean)""")
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

    parsed_args = parser.parse_args()
    return parsed_args

def main():
    """Validates user input and checks vSphere for percentage used of a
    specified datastore.
    """
    _args = parse_arguments()

    if _args.file:
        try:
            with open(_args.file, 'r', encoding='utf8') as config_file:
                _config = yaml.safe_load(config_file)
        except IOError:
            _config = {}
    else:
        _config = {}

    _valid_config = validate_config(_args, _config)

    _datastore = _args.datastore

    _warn_percent = _args.warn
    _crit_percent = _args.crit

    command = "govc datastore.info -json"

    os.environ['GOVC_URL'] = _valid_config['host']
    os.environ['GOVC_USERNAME'] = _valid_config['username']
    os.environ['GOVC_PASSWORD'] = _valid_config['password']
    os.environ['GOVC_INSECURE'] = str(_valid_config['insecure'])

    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print("VSPHERE_DATASTORE UNKNOWN: ", exc.output, end='', sep='')
        sys.exit(3)

    _dsinfo = json.loads(output)

    output = get_datastore_info(_dsinfo, _datastore, _warn_percent, _crit_percent)
    if output["used_percent"] is not None:
        print("VSPHERE_DATASTORE ", output['status_text'],  " Used: ",
              output["used_percent"], "%", sep='')
        sys.exit(output['status_code'])
    else:
        print("VSPHERE_DATASTORE ", output['status_text'], sep='')
        sys.exit(output['status_code'])

if __name__ == "__main__":

    main()
