"""
This module copies files to hotfolder, wait till all the files are picked by pitcher to transfer to IRD,
waits till all the files are received by IRD. It verifies pitcher and catcher logs for these verifications.
Finally, it verifies for the missing files in the transfer and list out all the missing files.
"""

import shutil
import sys
import time
import re
import csv
import os
import telnetlib as tlib



IRD_LOG_DIR = '/Gaian/TOS/OO/LOG'
CATCHER_LOG_NAME = 'FR174.log'
PITCHER_LOG = '/home/gaian/CDFApiSupp_SAYA_1.0.1_22/logs/CSAYARAGHAVENDER.log'
WAIT_PERIOD = 60
TIME_OUT = 15000
IRD_IP = "192.168.25.157"


filetype_dir_map = {'jpg': '/Gaian/TOS/OO/IMAGES',
                    'jpeg': '/Gaian/TOS/OO/IMAGES',
                    'mp3': '/Gaian/TOS/OO/AUDIO',
                    'mp4': '/Gaian/TOS/OO/VIDEO',
                    'BPL': '/Gaian/TOS/OO/BPL',
                    'pvr': '/Gaian/TOS/OO/PVR/HD'}


# function to clear contents of catcher log
def clear_catcher_log_contents(log):
    """
    clear the content of catcher log file
    :param log: catcher log file
    """
    tn = tlib.Telnet(IRD_IP)
    tn.read_until(b"login: ")
    tn.write("root" + b"\n")
    tn.write(b"cd {}\n".format(IRD_LOG_DIR))
    tn.write(b"> {}\n".format(CATCHER_LOG_NAME))
    tn.write(b"exit\n")

# function to find a pattern in pitcher log
def find_in_pitcher(log, pattern):
    """
    searches for pattern in pitcher log
    :param log: pitcher log
    :param pattern: pattern to search
    :return: true if pattern is found in pitcher log
    """
    with open(log) as f:
        # f.seek(0, os.SEEK_END)
        # file_size = f.tell()
        # file_size - bytes_read
        # f.seek(0, bytes_read)
        for line in f:
            c_pattern = re.compile(pattern)
            match = re.search(c_pattern, line)
            if match:
                return True

# function to find a pattern in catcher log
def find_in_catcher(IRD_IP, pattern):
    """
    searches for pattern in catcher log of specified IRD
    :param IRD_IP: IP of IRD
    :return: true if pattern is found in catcher log
    """
    tn = tlib.Telnet(IRD_IP)
    tn.read_until(b"login: ")
    tn.write("root" + b"\n")
    tn.write(b"cd {}\n".format(IRD_LOG_DIR))
    tn.write(b"cat {}\n".format(CATCHER_LOG_NAME))
    tn.write(b"exit\n")
    catcher_content = tn.read_all().split('\n')
    for line in catcher_content:
        c_pattern = re.compile(pattern)
        match = re.search(c_pattern, line)
        if match:
            return True


# main script execution starts here
# clear contents of pitcher log and catcher log
with(open(PITCHER_LOG, 'w')) as f:
    f.seek(0)
    f.truncate()
clear_catcher_log_contents(os.path.join(IRD_LOG_DIR, CATCHER_LOG_NAME))


# copy files to hot folder
file_name = sys.argv[1]
dest_folder = sys.argv[2]
start_index = int(sys.argv[3])
end_index = int(sys.argv[4])
print start_index
print end_index
num_of_files_to_copy = end_index - start_index
fname, ext = file_name.split('.')[0], file_name.split('.')[1]
files_pitcher_catcher_map = {}
while(start_index <= end_index):
    new_fname = "{}_{}.{}".format(fname, start_index, ext)
    shutil.copyfile(file_name, "{}/{}".format(dest_folder, new_fname))
    IRD_file = "{}_{}.{}".format(fname[9:], start_index, ext)
    files_pitcher_catcher_map[IRD_file] = new_fname
    start_index = start_index+1
    time.sleep(0.001)


# wait till all the files are sent by pitcher
pitcher_log_pattern = "Transmission Completed for file .*{}_{}.{}".format(fname, end_index-1, ext)
wait_time = 0
while True:
    if find_in_pitcher(PITCHER_LOG, pitcher_log_pattern):
        print "All files are transmitted by pitcher"
        break
    elif wait_time <= TIME_OUT:
        time.sleep(WAIT_PERIOD)
        wait_time = wait_time+WAIT_PERIOD
    else:
        raise Exception("All files are not transmitted by pitcher in {} seconds".format(TIME_OUT))


# wait till all the files are received by catcher
wait_time = 0
catcher_log_pattern = "renaming \[{}/.*{}.*_{}.{}\]".format(filetype_dir_map[ext], fname[9:], end_index-1, ext)
print "catcher_log_pattern----->", catcher_log_pattern
while True:
    if find_in_catcher(IRD_IP, catcher_log_pattern):
        print "All files are received by catcher"
        break
    elif wait_time <= TIME_OUT:
        time.sleep(WAIT_PERIOD)
        wait_time = wait_time + WAIT_PERIOD
    else:
        raise Exception("All files are not received by catcher in {} seconds".format(TIME_OUT))

# find missed files
missed_files = []
tn = tlib.Telnet(IRD_IP)
tn.read_until(b"login: ")
tn.write("root" + b"\n")
tn.write(b"cd {}\n".format(filetype_dir_map[ext]))
tn.write(b"ls \n")
tn.write(b"exit\n")
ird_files = tn.read_all()
for file in files_pitcher_catcher_map:
    if not file in ird_files:
        missed_files.append(files_pitcher_catcher_map[file])

print "missed_files are ---->", missed_files


# results will be added to a xls file
with open("results.xls", 'wt') as f:
    writer = csv.writer(f)
    writer.writerow(('IRD_IP', 'Pattern', 'Number_of_files_sent', 'Number_of_missed_files', "missed files"))
    print "num_of_files_to_copy---->", num_of_files_to_copy
    writer.writerow((IRD_IP, ext, num_of_files_to_copy, len(missed_files), ''))
    if len(missed_files) > 0:
        for missed_file_name in missed_files:
            writer.writerow(('', '', '', '', missed_file_name))
    f.close()