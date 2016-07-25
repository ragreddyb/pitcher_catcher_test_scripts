import sys
import time
# update the catcher configuration file
# usage python update_catcher_conf.py MAYA/SAYA
catcher_conf = '/tango/catcher.conf'
environment = sys.argv[1]
print environment
with open(catcher_conf, 'r+') as f:
    content = f.read()
    content_list = content.split()
    if environment == 'MAYA':
        print "entered to MAYA"
        if len(content_list) == 5:
            content_list = content_list[0:-1]
    else:
        print "entered to SAYA"
        if len(content_list) == 5:
            content_list = content_list[0:-1]
            content_list.append('1')
        elif len(content_list) == 4:
            content_list.append('1')

    new_content = ' '.join(content_list)
    print new_content
    f.seek(0)
    f.write(new_content)
    f.truncate()
