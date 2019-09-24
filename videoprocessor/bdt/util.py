import os
import skvideo.io as videoio
import base64
import numpy as np
import happybase


VIDEO_TABLE_NAME = 'video_frame'
DEFAULT_FRAMERATE = b'30/1'
DEFAULT_PATH = '/var/www/html'


def get_video(video_name, start_secs, end_secs, vid_quality=1, save_dir=DEFAULT_PATH, table_name=VIDEO_TABLE_NAME):
    """Retrieve video from start seconds up to end seconds. 
    Also adjust the shrink the video frame rate according to vid_quality.
    """
    pool = happybase.ConnectionPool(size=3)
    with pool.connection() as connection:
        table = connection.table(table_name)
        # first get the frame rate
        metadata = table.row(video_name, columns=[b'mtd:fr', b'mtd:rows', b'mtd:cols', b'mtd:channels'])
        #import pdb; pdb.set_trace()
        framerate = metadata.get(b'mtd:fr', DEFAULT_FRAMERATE).decode()
        row_count = int(metadata[b'mtd:rows'].decode())
        col_count = int(metadata[b'mtd:cols'].decode())
        channels = int(metadata[b'mtd:channels'].decode())
        if len(framerate.split('/')) > 1:
            num, denum = framerate.split('/')
            framerate = int(num)/int(denum)
        framerate = round(framerate)  #frame rate = how many frames make one sec
        start_frame = start_secs * framerate
        end_frame = end_secs * framerate
        framerate = round(framerate/vid_quality)       # adjust the frame rate according to the video quality
        cols = []
        for i in range(start_frame, end_frame, vid_quality):
            cols.append(('cts:%s' %  i).encode())
        video_data = table.row(video_name, columns=cols)
        #temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(save_dir, os.path.basename(video_name))
        vwriter = videoio.FFmpegWriter(filepath, inputdict={'-r': str(framerate), }, 
                                       outputdict={
                                           '-vcodec': 'libx264',
                                           '-pix_fmt': 'yuv420p',
                                           '-r': str(framerate),
                                           })
        for col in cols:
            b64_string = video_data.get(col, '')
            if b64_string:
                try:
                    frame = np.frombuffer(base64.b64decode(b64_string), np.uint8)
                    frame = np.reshape(frame, (row_count, col_count, channels))
                    vwriter.writeFrame(frame)
                except Exception as ex:
                    print('error reading frame: %s, error: %s' % (col, str(ex)))
        vwriter.close()
        return filepath
