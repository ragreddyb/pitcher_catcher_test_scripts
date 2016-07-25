'''
This script can be used for deleting already copied videos files to catchers, in C catcher testing.
We are doing this to free memory, otherwise test may hang because of lack of memory
config.ini should be in the same directory of this script
'''

import csv
from ConfigParser import SafeConfigParser
import os
import time
import logging

filetype_dir_map = {'jpg': '/Gaian/TOS/OO/IMAGES',
                    'jpeg': '/Gaian/TOS/OO/IMAGES',
                    'mp3': '/Gaian/TOS/OO/AUDIO',
                    'mp4': '/Gaian/TOS/OO/VIDEO',
                    'BPL': '/Gaian/TOS/OO/BPL',
                    'pvr': '/Gaian/TOS/OO/PVR',
                    'png': '/Gaian/TOS/OO/IMAGES'}


# read configuration file and get all the values
parser = SafeConfigParser()
parser.read('config.ini')
catcher_start_index = int(parser.get('catcher_settings', 'CATCHER_START_INDEX'))
catcher_end_index = int(parser.get('catcher_settings', 'CATCHER_END_INDEX'))
wait_duration = int(parser.get('catcher_settings', 'FREQUENCY_TO_REMOVE_VIDEO_FILES'))
files_pitcher_catcher_map = {}

LOG_FILENAME = 'remove_files_log.out'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    filemode='w'
                    )
# delete deleted_mp4_files.csv, if it exists already
logging.debug('removing deleted_mp4_files.csv, if it exists already')
try:
    os.remove("deleted_mp4_files.csv")
except OSError:
    pass

logging.debug('catcher start index --> {}'.format(catcher_start_index))
logging.debug('catcher end index --> {}'.format(catcher_end_index))
logging.debug('about to remove files for every {} seconds'.format(wait_duration))
logging.debug('initially waiting for {} seconds.....'.format(wait_duration))
time.sleep(wait_duration)

# deletes the video files here
with open("deleted_mp4_files.csv", 'wt') as f:
    writer = csv.writer(f)
    writer.writerow(('catcherID','deleted_file'))
    while(True):
        catcher_start_index = int(parser.get('catcher_settings', 'CATCHER_START_INDEX'))
        while(catcher_start_index <= catcher_end_index):
            temp_path = filetype_dir_map['mp4']
            dest_path = os.path.join(os.path.dirname(temp_path), str(catcher_start_index), temp_path.split('/')[-1])
            logging.debug('Now searching in {} directory'.format(dest_path))
            os.chdir(dest_path)
            files = os.listdir(dest_path)
            logging.debug('All files in {} directory are---> {}'.format(dest_path, files))
            missed_files = []
            for file in files:
                if '_temp' in file:
                    logging.debug('There is a temp file {} in {}'.format(file, dest_path))
                    continue
                writer.writerow((catcher_start_index, file))
                full_path_to_file = os.path.join(dest_path, file)
                logging.debug('About to delete {}'.format(full_path_to_file))
                os.remove(full_path_to_file)
            catcher_start_index += 1
        logging.debug('Waiting for {} seconds.....'.format(wait_duration))
        time.sleep(wait_duration)

logging.debug('All deleted video files are written to {}'.format('deleted_mp4_files.csv'))
print "All deleted video files are written to deleted_mp4_files.csv"






