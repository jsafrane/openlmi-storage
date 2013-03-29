# Anaconda initialization routines
# Useful for python -i anaconda_init.py
#

import logging
import blivet
import os

# setup logging
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
log_handler.setFormatter(formatter)

blivet_logger = logging.getLogger("blivet")
blivet_logger.addHandler(log_handler)
blivet_logger.setLevel(logging.DEBUG)
logger = logging.getLogger("program")
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)

# hack to insert RAID modules
for module in ('raid0', 'raid1', 'raid5', 'raid10'):
    os.system('modprobe ' + module)

b = blivet.Blivet()
b.reset()

print "\n\n***********************"
print "disk = b.devicetree.getDeviceByName('sda')"
disk = b.devicetree.getDeviceByName('sda')


