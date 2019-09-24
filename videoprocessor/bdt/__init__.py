import os
import zlib
import time
import json
import base64
import numpy as np
import shutil
import glob
import skvideo.io as vreader
from kafka import KafkaProducer
from bdt.conf import (UPLOAD_DIR, COMPLETED_DIR, TOPIC)


#although we might be compressing message sent to kafka
#each image frame can be max of 10mb
producer = KafkaProducer(max_request_size=51200000, compression_type='gzip') 


def process_file(filepath):
    filename = os.path.basename(filepath)
    video = vreader.vread(filepath)
    metadata = {'total_frames': video.shape[0], 'rows': video.shape[1], 
                'cols': video.shape[2], 'channels': video.shape[3]}
    extras = vreader.ffprobe(filepath).get('video', {})
    metadata['frame_rate'] = extras.get('@avg_frame_rate', '')
    metadata['duration'] = extras.get('@duration', '')
    payload = {'video_id': filename}
    # now we would send each video in frames
    for idx, frame in enumerate(video):
        metadata['id'] = idx
        img_str = base64.b64encode(frame.flatten()).decode('utf8')  # decode to plane string
        payload['data']  = img_str
        payload['metadata'] = metadata
        print('%s, sending frame: %s' % (filename, idx))
        producer.send(TOPIC, json.dumps(payload).encode('utf8'))
        print('%s, sent frame: %s' % (filename, idx))
    #once done move the file to 
    print('%s, moving to completed folder' % (filename, ))
    shutil.move(filepath, COMPLETED_DIR)
        

def process_all():
    while True:
        for filepath in glob.glob('%s/*.*' % UPLOAD_DIR):
            try:
                process_file(filepath)
            except Exception as ex:
                print('error processing file: %s, desc: %s' % (filepath, str(ex)))
        time.sleep(5)   # sleep 5 seconds



if __name__ == '__main__':
    process_all()