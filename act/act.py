#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2021 Alex Roland
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import requests
import getpass
import re
import os
from threading import Thread, currentThread, Lock
from queue import Queue
from datetime import datetime
from netmiko import ConnectHandler
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category = InsecureRequestWarning) # This will disable certificate warning output when running the script

parser = argparse.ArgumentParser(description = 'Checks ACLs for an IP match')
parser.add_argument('-i', help = 'ip to check (can be comma separated)')
parser.add_argument('-s', help = 'XMC hostname / IP (default: xmc)', default = 'xmc')
parser.add_argument('-u', help = 'username for SSH authentication (default: admin)', default = 'admin')
parser.add_argument('-t', help = 'number of threads to run (default: 20)', type=int, default = 20)
parser.add_argument('-w', help = 'filename to write report to (default: [time]-[ip]-report.log)', default = 'report.log')
parser.add_argument('-n', help = 'do not validate HTTPS certificates (default: false)', default = False, action = 'store_true')
parser.add_argument('-V', help = 'display version information', default = False, action = 'store_true')
args = parser.parse_args()

def version_info():
    NAME = 'ACL Check Tool'
    VERSION = '2.3.5'
    DATE = '10/22/2021'

    print('|' + '-'*30 + '|')
    print('|' + ' '*8 + NAME + ' '*8 + '|')
    print('|' + '-'*30 + '|')
    print('|' + ' '*4 + VERSION + ' '*5 + '|' + ' '*3 + DATE + ' '*2 + '|')
    print('|' + '-'*30 + '|')
    exit(0)

if args.V == True: # Script version information
    version_info()

if args.i is None: # Checks if user provided an IP to check against
    print('Please provide at least one IP to check')
    exit(0)

ips = args.i.split(',')
current_date = datetime.now().strftime('%Y-%m-%d')
failed = False # Used to let the user know if there is anything in the failure log

NUM_THREADS = args.t # Used to set the maximum amount of parallel connections
PRINT_LOCK = Lock() # This will prevent the output from being sent out of order

# Script colors
warningColor = "\033[91m"
resetColor = "\033[0m"
os.system('') # Needed to trigger color detection

def log_folder():
    """
    Creates a logs folder if one does not exist.
    """
    if os.path.isdir('logs'):
        return
    else:
        try:
            os.mkdir('logs')
        except BaseException as e:
            log_failed(e)
            global failed
            failed = True

def daily_runtime_folder():
    """
    Create a folder nested in the logs folder to organzie logs by date.
    """
    if os.path.isdir('logs/' + current_date):
        return
    else:
        try:
            os.mkdir('logs/' + current_date)
        except BaseException as e:
            log_failed(e)
            global failed
            failed = True

def log_file(file): # Function to output to the screen and log the output to a file
    """
    Log builder that grabs all detailed output and writes it to a file.
    """
    def write_log(msg):
        with PRINT_LOCK:
            with open('logs/' + current_date + '/' + file, 'a') as f:
                print(msg, file=f)
            return msg # Returns the user message so the message can be assigned to a variable for further data processing
    return write_log # Returns nested function

def log_sum(file): # Function to output to the screen and log the output to a file
    """
    Log builder to summarize output to screen. This is opposed to the main log builder that grabs all detailed output.
    """
    def write_log(msg):
        with PRINT_LOCK:
            with open('logs/' + current_date + '/' + file, 'a') as f:
                print(msg, file=f)
                print(msg)
            return msg # Returns the user message so the message can be assigned to a variable for further data processing
    return write_log # Returns nested function

def grab_routers(nickName):
    """
    Grab a list of routers based on checking for identifying information. The identifying information depends on the device naming 
    convention. For example, for il-chi-x690-c1 you would check for 'c' in the last index after splitting on the '-'.
    """
    if 'r' in nickName.split('-')[-1] or 'c' in nickName.split('-')[-1]: # Grab r(outer) or c(ore)
        is_router = True
    else:
        is_router = False
    return is_router

def discover_vendor(nickName, nosIdName):
    """
    Return the network operating system based on checking for identifying information. The identifying information depends on the device naming 
    convention. For example, for il-chi-x690-c1 you would check for 'x' in the second to last index after splitting on the '-'.
    We grab the NOS so commands are run correctly based on the NOS syntax.
    """
    if '-' in nickName and 'pnw.edu' not in nickName and 'purdue.edu' not in nickName:
        letter = nickName.split('-')[-2][0]
    else:
        logger(nickName + ' does not conform to naming conventions')
        nos = 'null'
        return nos
    if letter == 'x':
        nos = 'extreme_exos'
    elif letter == 'e':
        nos = 'enterasys'
    elif letter == 'c':
        if 'Nexus' in nosIdName:
            nos = 'cisco_nxos'
        elif 'Cisco' in nosIdName:
            nos = 'cisco_ios'
    else:
        nos = 'null'
    return nos

def check_ip(output, ip_list, ip, hostname):
    """
    Check all provided IPs against running configuration. This will also format the output by doing a reverse search to show which ACL the 
    match came from.
    """
    acl_list = output.splitlines() # Read each config line into a new list
    ipcounter = 0
    for index, item in enumerate(acl_list): # Grabs the index value along with the list value. Used to start the reverse search below
        for addr in ip_list:
            if re.search(rf'\b{ip_list[ipcounter]}\b', item): # Use regex word boundaries to search for an exact IP match anywhere in the configuration
                for line in acl_list[index::-1]: # Reverses search on the ACL output so it can grab the name of the ACL it found a match in
                    if ' ' not in line[0]:
                        out_sum(f'{ip}({hostname}) --> {line}')
                        logger(f'{ip}({hostname}) --> {line}')
                        break
                out_sum(f'{ip}({hostname}) --> {item}')
                logger(f'{ip}({hostname}) --> {item}')
            ipcounter += 1
        ipcounter = 0

def run_threads(total_devices, mt_function, dq, dd, ip_list): # dq is the device queue and dd is the device details
    """
    Builds and kicks off the hyper-threading. Number of threads is defaulted to 20, but can be overridden with the -t argument.
    """
    total_threads = min(NUM_THREADS, total_devices) # If the amount of loaded devices is less than the max thread count, then limit the amount of threads to device count
    for i in range(total_threads):
        thread_name = f'Thread-{i}'
        worker = Thread(name=thread_name, target=mt_function, args=(dq, dd, ip_list))
        worker.start()
    worker.join() # Waits for all threads to stop before ending script

def send_commands(dq, dd, ip_list):
    """
    Sends commands to the network devices.
    """
    while True:
        thread_name = currentThread().getName()
        ipcounter = 0
        global failed

        if dq.empty(): # Check if device queue is empty
            logger(f'{thread_name}: Closing since there are no jobs left in the queue.')
            return

        nc_params = dq.get() # Create variable to fill with device queue information per iteration
        device_detail = dd.get() # Pull original device line, used for more specific device information so we can reference different points of data
        ip = nc_params['ip'] # Pull the IP for output formatting
        hostname = device_detail['nickName'] # The nickname is also the hostname of the device

        logger(f'{thread_name} {ip}: Connecting...')
        try:
            nc = ConnectHandler(**nc_params) # Establishes SSH connectivity
            logger(f'{thread_name} {ip}: Connected!')
            logger(f'{thread_name} {ip}: Sending commands...')
            try:
                if nc_params['device_type'] == 'extreme_exos':
                    policy = re.findall(r"[a-zA-Z0-9_\\\-\.\(\):]+\.pol", nc.send_command('ls'))
                    logger(f'{thread_name} {ip} output:\n{policy}')
                    if policy != []:
                        for i in range(len(policy)):
                            policyfile = policy[i].strip('.pol')
                            for addr in ip_list:
                                ipcheck = nc.send_command_timing(f'show policy {policyfile} | i {ip_list[ipcounter]}')
                                if re.search(rf'\b{ip_list[ipcounter]}\b', ipcheck) and not "Unrecognized" in ipcheck:
                                    output = policyfile + " has line " + ipcheck
                                    logger(f'{thread_name} {ip} output:\n' + output)
                                    out_sum(f'{ip}({hostname}) --> {output}')
                                ipcounter += 1
                            ipcounter = 0
                    else:
                        logger('No policy found')
                elif nc_params['device_type'] == 'enterasys':
                    output = nc.send_command('show access-lists')
                    check_ip(output, ip_list, ip, hostname)
                elif nc_params['device_type'] == 'cisco_ios':
                    output = nc.send_command('show access-lists')
                    check_ip(output, ip_list, ip, hostname)
                elif nc_params['device_type'] == 'cisco_nxos':
                    output = nc.send_command('show access-lists')
                    check_ip(output, ip_list, ip, hostname)
                else:
                    raise
            except BaseException as e:
                log_failed(f'{thread_name} {ip}: {e}')
                failed = True
                nc.disconnect() # Gracefully closes the SSH connection
                dq.task_done() # Indicate that a formerly enqueued task is complete
                return
            nc.disconnect() # Gracefully closes the SSH connection
            logger(f'{thread_name} {ip}: Done!')
            dq.task_done() # Indicate that a formerly enqueued task is complete
        except BaseException as e:
            log_failed(f'{thread_name} {ip}:\n {e}')
            failed = True
            dq.task_done() # Indicate that a formerly enqueued task is complete

if args.w == 'report.log': # Creates a unique report name
    args.w = f'{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}-{ips[0]}-report.log' # Standard log file to log all events
    failedfile = f'{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}-{ips[0]}-failed-report.log' # If there are any issues, output to a failed file
    sumfile = f'{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}-{ips[0]}-summary-report.log' # Output the success to separate file
else:
    failedfile = f'{args.w}-failed-report.log'
    sumfile = f'{args.w}-summary-report.log'

logger = log_file(args.w) # Set standard log file
log_failed = log_file(failedfile) # Set log file if there is a failed device
out_sum = log_sum(sumfile) # Set log file for summary output

def main():
    password = getpass.getpass(f'{args.u} password:')
    
    log_folder()
    daily_runtime_folder()

    api_url = 'https://' + args.s + ':8443/nbi/graphql' # URL of the XMC server, pulled from -s flag in argparse

    http_params = {
        # XMC API query to run, more info at https://{xmc_server}:8443/nbi/graphiql/index.html then click on Docs in the top right
        'query': 'query { network { devices { ip nickName nosIdName } } }'
    }

    NET_DEVICE = { # Basic device dictionary, this is copied in the main function and values are then filled in
        'device_type': '',
        'ip': '',
        'username': args.u,
        'password': '',
        'conn_timeout': 10,
    }

    ip_list = [addr.replace('.', '\.') for addr in ips] # Converts each IP in the list to escape the dot between the octects
    global failed

    logger('Connecting...')
    out_sum('Connecting...')
    start_time = datetime.now()

    device_queue = Queue(maxsize=0) # Opens a queue for the device network connection information
    device_details = Queue(maxsize=0) # Opens a queue for the detailed device information

    try:
        r = requests.get(api_url, auth = (args.u, password), params = http_params, verify = not args.n) # API call to XMC server
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
        result = r.json()['data']['network']['devices'] # Convert result to JSON format
        for device in result:
            if device['nickName'] is None:
                continue
            router_check = grab_routers(device['nickName'])
            if router_check == False:
                continue
            vendor = discover_vendor(device['nickName'], device['nosIdName'])
            if vendor == 'null':
                continue
            new_device = NET_DEVICE.copy()
            new_device['device_type'] = vendor # Pulls vendor from hostname, which is used as the connection profile for Netmiko
            new_device['ip'] = device['ip'] # Pulls IP to connect to
            new_device['password'] = password # Puts the prompted SSH user password into the dictionary
            device_queue.put(new_device) # Loads device network connetion information into the queue
            device_details.put(device)
        
        total_devices = device_queue.qsize() # Used in the max thread calculation
        logger(f'\nSearching {total_devices} routers')
        out_sum(f'\nSearching {total_devices} routers')

        run_threads(total_devices=total_devices, mt_function=send_commands, dq=device_queue, dd=device_details, ip_list=ip_list) # Calls the multithreading function
        device_queue.join() # Blocks until all items in the queue have been gotten and processed

        logger(f'\nElapsed time: {str(datetime.now() - start_time)}') # Total runtime for the script
        out_sum(f'\nElapsed time: {str(datetime.now() - start_time)}') # Total runtime for the script
    except requests.exceptions.HTTPError as r:
        print(f'Unable to connect to {api_url}, check connection or username/password')
        log_failed(f'Unable to connect to {api_url}, check connection or username/password')
        log_failed(r)
    except BaseException as e:
        print(f'Failed to fetch data, check connection to "{args.s}"')
        log_failed('Failed to fetch data:')
        log_failed(e)
        failed = True
    
    if failed == True:
        print(f'{warningColor}There were some issues, check the failed log output for details{resetColor}')

if __name__ == "__main__": # Check if script is called by the user or imported
    main()