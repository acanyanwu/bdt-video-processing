import numpy as np
import base64
import sys
import cv2
from pyspark import SparkContext,SparkConf
#    Spark Streaming
from pyspark.streaming import StreamingContext
#    Kafka
from pyspark.streaming.kafka import KafkaUtils
#    json parsing
import json
import time
from pydarknet import Detector, Image
import findspark
import happybase

ZOOKEEPER_ENDPOINT = 'localhost:2181'

HBASE_HOST = 'localhost'

HBASE_TABLE = 'yolo_video'

conf = SparkConf().setAppName('PythonSparkStreamingKafka_RM_01').set('spark.driver.supervise','true').set('spark.executor.memory', '24g').set('spark.driver.memory', '8g').setMaster('local[*]')
#conf.set("spark.executor.heartbeatInterval","3600s")
sc = SparkContext(conf=conf)
findspark.init()
# sc = SparkContext(appName="PythonSparkStreamingKafka_RM_01", master='local[*]')
sc.setLogLevel("WARN")
ssc = StreamingContext(sc, 5)
broker, topic = sys.argv[1:]
kafkaParams={'fetch.message.max.bytes':'50240000','auto_offset_reset': 'latest'}
kafkaStream = KafkaUtils.createStream(ssc, broker, kafkaParams=kafkaParams, groupId='any12dfhdjhfd3', topics={topic:1})

def process(record):
    values=json.loads(record[1])
    data=values['data']
    videoid=values['video_id']
    metadata=values['metadata']
    frameNum=metadata['id']
    nparr = np.reshape(np.frombuffer(base64.b64decode(data.encode('utf8')),
                                     np.uint8),(metadata['rows'],metadata['cols'],metadata['channels']))
    start_time = time.time()
    frame = Image(nparr)
    net = Detector(bytes("yolov3.cfg", encoding="utf-8"), bytes("yolov3.weights", encoding="utf-8"), 0,
                   bytes("coco.data", encoding="utf-8"))
    results = net.detect(frame)
    del frame
    end_time = time.time()
    # print("Elapsed Time:",end_time-start_time)
    categories=[]
    for cat, score, bounds in results:
        x, y, w, h = bounds
        categories.append(str(cat.decode("utf-8")))
        cv2.rectangle(nparr, (int(x-w/2),int(y-h/2)),(int(x+w/2),int(y+h/2)),(255,0,0))
        cv2.putText(nparr, str(cat.decode("utf-8")), (int(x), int(y)), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255))
   
    #cv2.imwrite('yolo-output/'+str(frameNum)+'.jpg', nparr)
#    print('process done')
#     save to hbase
    yoloframe = 'cts:%s' % frameNum
    #metadata1 = 'mtd:%s' % frameNum
    labels = 'lbs:%s' % frameNum
#    metadata = json.dumps(metadata).encode()
    categ= json.dumps(categories).encode()
    
    key_vals = {yoloframe.encode(): base64.b64encode(nparr), labels.encode(): categ}
    key_vals[b'mtd:rows'] = str(metadata['rows']).encode('utf8')
    key_vals[b'mtd:cols'] = str(metadata['cols']).encode('utf8')
    key_vals[b'mtd:channels'] = str(metadata['channels']).encode('utf8')
    key_vals[b'mtd:fr'] = str(metadata['frame_rate']).encode('utf8')
    key_vals[b'mtd:dur'] = str(metadata['duration']).encode('utf8')
    key_vals[b'mtd:fc'] = str(metadata['total_frames']).encode('utf8')
    return (videoid.encode(), key_vals)


def save_hbase(entries): 
    pool = happybase.ConnectionPool(size=3, host=HBASE_HOST)
    for entry in entries:
        with pool.connection() as connection:
             table = connection.table(HBASE_TABLE)
             table.put(entry[0], entry[1])

     

# #do any transformation of the recieved data frame
parsed = kafkaStream.map(process).foreachRDD(lambda rdd: rdd.foreachPartition(save_hbase))

ssc.start()
ssc.awaitTermination()

ssc.stop()

