package bdt.splitter;

import java.util.HashMap;
import java.util.Map;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.spark.JavaHBaseContext;
import org.apache.hadoop.hbase.TableName;
import org.apache.spark.SparkConf;
import org.apache.spark.storage.StorageLevel;
import org.apache.hadoop.hbase.util.Bytes;
import org.apache.spark.streaming.Seconds;
import org.apache.spark.streaming.api.java.JavaDStream;
import org.apache.spark.streaming.api.java.JavaPairReceiverInputDStream;
import org.apache.hadoop.hbase.client.Put;
import org.apache.spark.streaming.api.java.JavaStreamingContext;
import org.apache.spark.streaming.kafka.KafkaUtils;

import com.jayway.jsonpath.JsonPath;


public class PlainFrameSaver
{
    
    public static void main(String[] args) throws InterruptedException {
        String kafkaEndpoint = "localhost:2181";
        String master = "local[2]";
        String topicList = "video-stream";
        String tableName = "video_frame";
        Integer streamDuration = 5;
        Map<String, String> kafkaParams = new HashMap<>();
        kafkaParams.put("zookeeper.connect", kafkaEndpoint);
//        kafkaParams.put("key.deserializer", StringDeserializer.class);
//        kafkaParams.put("value.deserializer", StringDeserializer.class);
        kafkaParams.put("group.id", PlainFrameSaver.class.getSimpleName());
        kafkaParams.put("auto.offset.reset", "largest");
        kafkaParams.put("max.request.size", "51200000");
        kafkaParams.put("max.partition.fetch.bytes", "51200000");
//        kafkaParams.put("kafka.max.request.size", "15728640");
        if(args.length > 0)
            kafkaEndpoint = args[0];
        if(args.length > 1)
            streamDuration = Integer.valueOf(args[1]);
        if(args.length > 2)
            topicList = args[2];
        if(args.length > 3)
            tableName = args[3];
        Map<String, Integer> topicMap = new HashMap<String, Integer>();
        for(String topic: topicList.split(","))
            topicMap.put(topic, 3);
        SparkConf conf = new SparkConf().setAppName(PlainFrameSaver.class.getName()).setMaster(master);
        JavaStreamingContext ssc = new JavaStreamingContext(conf, Seconds.apply(streamDuration));
        Configuration hConf = HBaseConfiguration.create();
        JavaHBaseContext hbaseContext = new JavaHBaseContext(ssc.sparkContext(), hConf);
        JavaPairReceiverInputDStream<String, byte[]> stream = KafkaUtils.createStream(ssc, String.class, byte[].class,
            kafka.serializer.StringDecoder.class, kafka.serializer.DefaultDecoder.class, kafkaParams, topicMap,
            StorageLevel.MEMORY_AND_DISK_SER());
        JavaDStream<Put> tStream = stream.map(t->{
            String entry = Bytes.toString(t._2);
            String videoId = JsonPath.read(entry, "$.video_id");
            Map<String, Object> metadata = JsonPath.read(entry, "$.metadata");
            String data = JsonPath.read(entry, "$.data");
            Put row = new Put(Bytes.toBytes(videoId));
            row.addColumn(Bytes.toBytes("mtd"), Bytes.toBytes("fr"), 
                Bytes.toBytes(metadata.getOrDefault("frame_rate", "30/1").toString()));
            row.addColumn(Bytes.toBytes("mtd"), Bytes.toBytes("fc"), 
                Bytes.toBytes(metadata.get("total_frames").toString()));
            row.addColumn(Bytes.toBytes("mtd"), Bytes.toBytes("rows"), 
                Bytes.toBytes(metadata.get("rows").toString()));
            row.addColumn(Bytes.toBytes("mtd"), Bytes.toBytes("cols"), 
                Bytes.toBytes(metadata.get("cols").toString()));
            row.addColumn(Bytes.toBytes("mtd"), Bytes.toBytes("dur"), 
                Bytes.toBytes(metadata.getOrDefault("duration", "0").toString()));
            row.addColumn(Bytes.toBytes("mtd"), Bytes.toBytes("channels"), 
                Bytes.toBytes(metadata.get("channels").toString()));
            row.addColumn(Bytes.toBytes("cts"), Bytes.toBytes(metadata.get("id").toString()), Bytes.toBytes(data));
            return row;
        });
        hbaseContext.streamBulkPut(tStream, TableName.valueOf(tableName), row->row);
        ssc.start();
        ssc.awaitTermination();
    }
}
