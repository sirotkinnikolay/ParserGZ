import json
import os
import logging
from typing import Union

from kafka import KafkaProducer
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka_actions:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'topic_1')

def get_kafka_producer() -> Union[KafkaProducer, None]:
    """
     Создаем Kafka producer.
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=3,
            acks='all'
        )
        return producer
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        return None