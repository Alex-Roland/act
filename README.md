# ACT
ACL Check Tool

# Limitations
This script is written to where an API call to Extreme Management Center (XMC) is made. You can modify the script to make an API call to an NMS that supports it, but doing so is not currently supported.

# Purpose
The ACT script is used to search routers for a matching IP. This will help maintain a good network security posture in the following ways:

- By checking what specific IP or network has access to resources
- Makes cleaning up rules easy after decommisioning an IP/server
- Easily able to duplicate access of checked IP

# Syntax
act.py [-h] -i _ip_ [-s] _xmc_server_ [-u] _username_ [-t] _thread_count_ [-w] _log_filename_ [-n] [-V]

# Examples
act.py -i 10.1.1.2 -s xmc.example.com -u admin -t 10 -w test_run.log

act.py -i 10.1.1.2,10.2.2.1 -u admin

act.py -i 10.0.0.0 -u admin
