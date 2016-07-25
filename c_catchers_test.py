'''
This script can be used for C catcher testing. It is used to verify that all the files available in hot folder are
reached to catchers. If any files are missing this script prepares list all the missed files in a file named results.csv
'''

import csv
from ConfigParser import SafeConfigParser
import os

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
hot_folder = parser.get('hf_files_settings', 'HOT_FOLDER_DIR')
batch_size = int(parser.get('hf_files_settings', 'BATCH_SIZE'))
wait_before_sending_another_batch = int(parser.get('time_settings', 'WAIT_PERIOD_AFTER_A_BATCH'))
wait_before_sending_other_file = float(parser.get('time_settings', 'WAIT_BETWEEN_EACH_FILE'))
num_of_times_each_file_to_copy = int(parser.get('hf_files_settings', 'NUM_OF_TIMES_EACH_FILE_TO_COPY'))

video_files_to_send = []
other_files_to_send = []
map_of_category_wise_files_to_send = {}
video_files_str = parser.get('hf_files_settings', 'VIDEO_FILES_TO_SEND')

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

catcher_start_index = int(parser.get('catcher_settings', 'CATCHER_START_INDEX'))
catcher_end_index = int(parser.get('catcher_settings', 'CATCHER_END_INDEX'))
environment = parser.get('catcher_settings', 'ENVIRONMENT')
files_pitcher_catcher_map = {}

def verify_in_mp4_files(catcher, file_name):
    with open('deleted_mp4_files.csv', 'rt') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            if catcher == int(row['catcherID']):
                if file_name == row['deleted_file']:
                    return True
    return False

try:
    os.remove("results.csv")
except OSError:
    pass

with open("results.csv", 'wt') as f:
    writer = csv.writer(f)
    writer.writerow(('catcher_ID', 'catcher_path', 'file_type', 'number_of_files_sent', 'number_of_missed_files', "missed files"))

    if video_files_to_send:
        while(catcher_start_index <= catcher_end_index):
            for file_name in video_files_to_send:
                fname, ext = file_name.split('.')[0], file_name.split('.')[1]
                temp_path = filetype_dir_map[ext]
                dest_path = os.path.join(os.path.dirname(temp_path), str(catcher_start_index), temp_path.split('/')[-1])
                files = os.listdir(dest_path)
                missed_files = []
                for i in range(map_of_category_wise_files_to_send[ext]):
                    src_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                    if environment == 'SAYA':
                        if ext == 'pvr':
                            dest_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                        else:
                            dest_file_name = "{}_{}.{}".format(fname[12:], i + 1, ext)
                    else:
                        if ext == 'BPL':
                            dest_file_name = "{}_{}.{}".format(fname[12:], i + 1, ext)
                        else:
                            dest_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                    if not dest_file_name in files:
                        if ext == 'mp4' and os.path.isfile("deleted_mp4_files.csv"):
                            if not verify_in_mp4_files(catcher_start_index, dest_file_name):
                                missed_files.append(src_file_name)
                        else:
                            missed_files.append(src_file_name)
                writer.writerow((catcher_start_index, dest_path, ext, map_of_category_wise_files_to_send[ext],
                                 len(missed_files), str(missed_files)))
            catcher_start_index += 1

    if other_files_to_send:
        catcher_start_index = int(parser.get('catcher_settings', 'CATCHER_START_INDEX'))
        while (catcher_start_index <= catcher_end_index):
            for file_name in other_files_to_send:
                fname, ext = file_name.split('.')[0], file_name.split('.')[1]
                temp_path = filetype_dir_map[ext]
                if ext == 'pvr':
                    sub_dirs = ["HD","SD"]
                    for sub_dir in sub_dirs:
                        dest_path.append(os.path.join(os.path.dirname(temp_path), str(catcher_start_index), temp_path.split('/')[-1], sub_dir))
                else:
                    dest_path = os.path.join(os.path.dirname(temp_path), str(catcher_start_index), temp_path.split('/')[-1])
                if type(dest_path) is list:
                    for destpath in dest_path:
                        os.chdir(destpath)
                        files = os.listdir(destpath)
                        missed_files = []
                        for i in range(map_of_category_wise_files_to_send[ext]):
                            src_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                            if environment == 'SAYA':
                                if ext == 'pvr':
                                    dest_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                                else:
                                    dest_file_name = "{}_{}.{}".format(fname[12:], i + 1, ext)
                            else:
                                if ext == 'BPL':
                                    dest_file_name = "{}_{}.{}".format(fname[12:], i + 1, ext)
                                else:
                                    dest_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                            if not dest_file_name in files:
                                missed_files.append(src_file_name)
                        writer.writerow((catcher_start_index, destpath, ext, map_of_category_wise_files_to_send[ext],
                                         len(missed_files), str(missed_files)))
                else:
                    os.chdir(dest_path)
                    files = os.listdir(dest_path)
                    missed_files = []
                    for i in range(map_of_category_wise_files_to_send[ext]):
                        src_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                        if environment == 'SAYA':
                            if ext == 'pvr':
                                dest_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                            else:
                                dest_file_name = "{}_{}.{}".format(fname[12:], i + 1, ext)
                        else:
                            if ext == 'BPL':
                                dest_file_name = "{}_{}.{}".format(fname[12:], i + 1, ext)
                            else:
                                dest_file_name = "{}_{}.{}".format(fname, i + 1, ext)
                        if not dest_file_name in files:
                            missed_files.append(src_file_name)
                    writer.writerow((catcher_start_index, dest_path, ext, map_of_category_wise_files_to_send[ext],
                                     len(missed_files), str(missed_files)))
            catcher_start_index += 1

print "verification is completed, please refer results.csv for more details"









