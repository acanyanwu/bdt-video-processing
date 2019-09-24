import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
COMPLETED_DIR = os.path.join(BASE_DIR, 'completed')
TMP_DIR = os.path.join(BASE_DIR, 'tmp')

KAFKA_URL = 'localhost:9092'
TOPIC='video-stream'