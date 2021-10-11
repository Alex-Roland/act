import os
from datetime import datetime
from act import args, ips, PRINT_LOCK

class Logger():
    def __init__(self, current_date, failedfile, sumfile):
        self.current_date = current_date
        current_date = datetime.now().strftime('%Y-%m-%d')

        if args.w == 'report.log': # Creates a unique report name
            args.w = f'{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}-{ips[0]}-report.log' # Standard log file to log all events
            self.failedfile = f'{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}-{ips[0]}-failed-report.log' # If there are any issues, output to a failed file
            self.sumfile = f'{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}-{ips[0]}-summary-report.log' # Output the success to separate file
        else:
            self.failedfile = f'{args.w}-failed-report.log'
            self.sumfile = f'{args.w}-summary-report.log'

    def log_folder(self):
        """
        Creates a logs folder if one does not exist.
        """
        if os.path.isdir('logs'):
            return
        else:
            try:
                os.mkdir('logs')
            except BaseException as e:
                print(e)
                global failed
                failed = True

    def daily_runtime_folder(self):
        """
        Create a folder nested in the logs folder to organzie logs by date.
        """
        if os.path.isdir('logs/' + self.current_date):
            return
        else:
            try:
                os.mkdir('logs/' + self.current_date)
            except BaseException as e:
                print(e)
                global failed
                failed = True

    def log_file(self, file): # Function to output to the screen and log the output to a file
        """
        Log builder that grabs all detailed output and writes it to a file.
        """
        def write_log(msg):
            with PRINT_LOCK:
                with open('logs/' + self.current_date + '/' + file, 'a') as f:
                    print(msg, file=f)
                return msg # Returns the user message so the message can be assigned to a variable for further data processing
        return write_log # Returns nested function

    def log_sum(self, file): # Function to output to the screen and log the output to a file
        """
        Log builder to summarize output to screen. This is opposed to the main log builder that grabs all detailed output.
        """
        def write_log(msg):
            with PRINT_LOCK:
                with open('logs/' + self.current_date + '/' + file, 'a') as f:
                    print(msg, file=f)
                    print(msg)
                return msg # Returns the user message so the message can be assigned to a variable for further data processing
        return write_log # Returns nested function
    
    logger = log_file(args.w) # Set standard log file
    log_failed = log_file(failedfile) # Set log file if there is a failed device
    out_sum = log_sum(self.sumfile) # Set log file for summary output