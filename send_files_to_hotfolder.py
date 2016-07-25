"""
This module copies files to hot folder. please specify all the configuration values in config.ini and
it should be in the same directory of this script.
"""
from ConfigParser import SafeConfigParser
import shutil
import time
import os
import glob
# sudo apt-get install python-paramiko
try:
    import paramiko
except ImportError, err:
    print '[*] Paramiko could not be imported'
    raise err

class RemoteMachine(object):
    '''
    RemoteMachine class over ssh;
    '''

    def __init__(self, ip, username='', password='', **kwargs):
        '''
        :param fqdn:
            fqdn or ip address of machine; preferably use fqdn
        :param username:
            ssh username.
        :param password:
            ssh password.

        :param kwargs:
            Optional settings used in stablishing ssh connection via
            paramiko.
        '''
        self.ip = ip
        self.username = username
        self.password = password
        self.port = kwargs.get('port', 22)
        self.connection = paramiko.SSHClient()
        self.open_connection()

    def open_connection(self):
        '''
        attempts to establish ssh connection to remote machine
        '''
        try:
            self.connection.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())

            self.connection.connect(
                self.ip, username=self.username, password=self.password,
                port=self.port
            )
        except Exception, e:
            msg = "Could not open a connection to remote machine {0}: {1}!".format(
                self.ip, e)
            raise Exception(msg)

    def execute_command(self, command):
        _, stdout, stderr = self.connection.exec_command(command)
        return stdout, stderr

    def copy_file(self, file_to_copy):
        # Setup sftp connection and transmit this script
        sftp = self.connection.open_sftp()
        sftp.put(file_to_copy, '/home/gaian/update_catcher_conf.py')
        sftp.close()


# read configuration file and get all the values
parser = SafeConfigParser()
parser.read('config.ini')
hot_folder = parser.get('hf_files_settings', 'HOT_FOLDER_DIR')
batch_size = int(parser.get('hf_files_settings', 'BATCH_SIZE'))
wait_before_sending_another_batch = int(parser.get('time_settings', 'WAIT_PERIOD_AFTER_A_BATCH'))
wait_before_sending_other_file = float(parser.get('time_settings', 'WAIT_BETWEEN_EACH_FILE'))
num_of_times_each_file_to_copy = int(parser.get('hf_files_settings', 'NUM_OF_TIMES_EACH_FILE_TO_COPY'))
catcher_conf_dir = parser.get('catcher_settings', 'CATCHER_CONF_DIR')
catcher_conf_file = parser.get('catcher_settings', 'CATCHER_CONF_FILE_NAME')
environment = parser.get('catcher_settings', 'ENVIRONMENT')
catcher_ips_str = parser.get('catcher_settings', 'CATCHER_IPs')
list_of_catchers = catcher_ips_str.split(',')
print list_of_catchers

# get lost of all catcher machines in a list
catcher_machines = []
for catcher in list_of_catchers:
    catcher_machines.append(catcher.strip().split('-'))
print catcher_machines

# update catcher configuration file on all catcher machines
for catcher_ip in catcher_machines:
    print catcher_ip[0]
    rm = RemoteMachine(catcher_ip[0], catcher_ip[1], catcher_ip[2])
    print rm
    rm.copy_file('update_catcher_conf.py')
    out, err = rm.execute_command('cd ~')
    print out.readlines()
    print err.readlines()
    out, err = rm.execute_command('python update_catcher_conf.py {}'.format(environment))
    print out.readlines()
    print err.readlines()

# prepares list of files to send and create a map of category of file to be send and number of files to be send
video_files_to_send = []
other_files_to_send = []
map_of_category_wise_files_to_send = {}
video_files_str = parser.get('hf_files_settings', 'VIDEO_FILES_TO_SEND')
print video_files_str
if video_files_str:
    video_files = video_files_str.split(',')
    for video_file in video_files:
        video_files_to_send.append(video_file.strip())
    num_of_video_files = len(video_files_to_send)
    total_video_files_to_copy = (num_of_times_each_file_to_copy / 2) * num_of_video_files
    for video_file in video_files_to_send:
        map_of_category_wise_files_to_send[video_file.split('.')[-1]] = num_of_times_each_file_to_copy / 2

other_files_str = parser.get('hf_files_settings', 'OTHER_FILES_TO_SEND')
if other_files_str:
    other_files = other_files_str.split(',')
    for other_file in other_files:
        other_files_to_send.append(other_file.strip())
    num_of_other_files = len(other_files_to_send)
    total_other_files_to_copy = num_of_times_each_file_to_copy*num_of_other_files
    for other_file in other_files_to_send:
        map_of_category_wise_files_to_send[other_file.split('.')[-1]] = num_of_times_each_file_to_copy

# deletes all files available in hot folder
for file in os.listdir(hot_folder):
    file_path = os.path.join(hot_folder, file)
    if os.path.isfile(file_path):
        os.remove(file_path)

# copy video/audio files to hotfolder, wait after sending a batch till specified number of files are copied
if video_files_to_send:
    count = 0
    while (count < num_of_times_each_file_to_copy/2):
        for file_name in video_files_to_send:
            fname, ext = file_name.split('.')[0], file_name.split('.')[1]
            new_fname = "{}_{}.{}".format(fname, count+1, ext)
            if count < total_video_files_to_copy:
                if count != 0 and count % batch_size == 0:
                    time.sleep(wait_before_sending_another_batch)
                shutil.copyfile(file_name, "{}/{}".format(hot_folder, new_fname))
                time.sleep(wait_before_sending_other_file)
            else:
                break
        count += 1

# copy other files to hotfolder, wait after sending a batch till specified number of files are copied
if other_files_to_send:
    count = 0
    while (count < num_of_times_each_file_to_copy):
        for file_name in other_files_to_send:
            fname, ext = file_name.split('.')[0], file_name.split('.')[1]
            new_fname = "{}_{}.{}".format(fname, count+1, ext)
            if count < total_other_files_to_copy:
                if count != 0 and count % batch_size == 0:
                    time.sleep(wait_before_sending_another_batch)
                shutil.copyfile(file_name, "{}/{}".format(hot_folder, new_fname))
                time.sleep(wait_before_sending_other_file)
            else:
                break
        count += 1

# make sure that all expected number of files are copied to hotfolder, raise an exception otherwise
map_of_category_wise_files_received = {}
for video_file in video_files_to_send:
    ext = video_file.split('.')[-1]
    files_count = len(glob.glob1(hot_folder, "*.{}".format(ext)))
    map_of_category_wise_files_received[video_file.split('.')[-1]] = files_count

for other_file in other_files_to_send:
    ext = other_file.split('.')[-1]
    files_count = len(glob.glob1(hot_folder, "*.{}".format(ext)))
    map_of_category_wise_files_received[other_file.split('.')[-1]] = files_count

if map_of_category_wise_files_to_send == map_of_category_wise_files_received:
    print "All files are copied succefully-->{}".format(map_of_category_wise_files_to_send)
else:
    raise Exception("Failure in copying all files--Expected to send-->{}, but only sent-->{}".format(map_of_category_wise_files_to_send, map_of_category_wise_files_received))


