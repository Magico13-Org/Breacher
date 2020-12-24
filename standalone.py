import sys

import image_processing

args = sys.argv
if len(args) < 2:
    print('Must provide filename. standalone.py file.png')
    exit(1)


shortest = False
debug = False

for arg in args:
    if arg == 'debug': debug = True
    elif arg == 'shortest': shortest = True

filename = args[1]
img = image_processing.open_file(filename)
seq, seq_t = image_processing.full_process(img, shortest, debug)
image_processing.wait_for_keypress()