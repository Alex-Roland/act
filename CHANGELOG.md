Unreleased - planned
--------------------
Change from Threading to Multiprocessing to make the script faster
Add additional NMS support (LibreNMS, Zabbix, etc...)


Version 2.3.5 - 2021-10-22
--------------------------
Updated: setup.py version is now pulled from the act.py file


Version 2.3.4 - 2021-10-12
--------------------------
Fixed: Issue with hyperthreading being called
Fixed: Exception handling for connection to NMS was not implemented correctly


Version 2.3.3 - 2021-10-12
--------------------------
Updated: Changed how JSON is handled from the XMC API call in the main function


Version 2.3.2 - 2021-10-11
--------------------------
Added: docstrings for functions
Added: setup.py
Updated: Restructured project files and folders


Version 2.3.1 - 2021-10-11
--------------------------
Updated: Changed the way processing more than one IP works. You now provide it with a single -i and comma separated


Version 2.3.0 - 2021-10-11
--------------------------
Added: Exception handling for making the log directory and subdirectories
Updated: Optimized code to save on memory and processing power
Fixed: The failed message works now and is colorized to stand out


Version 2.2.2 - 2021-08-11
--------------------------
Added: Output will inform user if there were any issues
Updated: Exception handling for the API call is more detailed now


Version 2.2.1 - 2021-08-09
--------------------------
Fixed: ACL name parsing has been optimized


Version 2.2.0 - 2021-08-08
--------------------------
Added: Grabs the ACL the matching rule is part of


Version 2.1.3 - 2021-08-05
--------------------------
Added: Check for logs folder in log builder


Version 2.1.2 - 2021-07-28
--------------------------
Fixed: Core router discovery wasn't implemented
Added: Check for and create daily runtime folders to better organize the log outputs


Version 2.1.1 - 2021-07-26
--------------------------
Added: -V option to print version information


Version 2.1 - 2021-07-22
------------------------
Added: XMC API call for dynamic inventory


Version 2.0 - 2021-02-01
------------------------
Added: Multi-threading capabilities


Version 1.0 - 2020-06-12
------------------------
Initial release