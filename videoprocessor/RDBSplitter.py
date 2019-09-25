import json
import base64
import numpy as np
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import happybase
from pyspark.conf import SparkConf


ZOOKEEPER_ENDPOINT = 'localhost:2181'

HBASE_HOST = 'localhost'

HBASE_TABLE = 'video_rgbsplit'

SPARK_MASTER = "local[*]"

GROUP_ID = 'RGBSplitter'

KAFKA_TOPIC = 'video-stream'


#pool = happybase.ConnectionPool(size=3, host=HBASE_HOST)


def get_frame_split_average(record):
    _, value = record
    data = json.loads(value)
    metadata = data['metadata']
    img = np.frombuffer(base64.b64decode(data['data'].encode('utf8')), np.uint8)
    img = np.reshape(img, (metadata['rows'], metadata['cols'], metadata['channels']))
    rgb_ave = np.average(img, axis=(0, 1))
    return (data['video_id'], metadata['id'], str(rgb_ave[0]), str(rgb_ave[1]), str(rgb_ave[2])) 


def save_partition_to_hbase(entries):
    pool = happybase.ConnectionPool(size=3, host=HBASE_HOST)
    with pool.connection() as connection:
        table = connection.table(HBASE_TABLE)
        for entry in entries:
            video_id, frame_id, red, green, blue = entry
            red_col = 'r:%s' % frame_id
            green_col = 'g:%s' % frame_id
            blue_col = 'b:%s' % frame_id
            table.put(video_id.encode(), 
                      {red_col.encode(): red.encode(),
                       green_col.encode(): green.encode(),
                       blue_col.encode(): blue.encode()})


def start():
#    conf = SparkConf().set("spark.jars", "/Users/anthonyanyanwu/eclipse-workspace/videostreamer/spark-streaming-kafka-0-8-assembly_2.11-2.4.4.jar")
    sc = SparkContext(SPARK_MASTER, "RGBSplitterApp")
    ssc = StreamingContext(sc, 10)
    kafkaStream = KafkaUtils.createStream(ssc, 
                                          ZOOKEEPER_ENDPOINT, GROUP_ID, {KAFKA_TOPIC: 3})
    kafkaStream.map(get_frame_split_average).foreachRDD(lambda rdd: rdd.foreachPartition(save_partition_to_hbase))
    ssc.start()
    ssc.awaitTermination()

start()
