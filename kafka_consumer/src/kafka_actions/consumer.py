import json
import os
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class KafkaMessageConsumer:
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka_actions:9092')
        self.topic = os.getenv('KAFKA_TOPIC', 'topic_1')
        self.group_id = os.getenv('KAFKA_GROUP_ID', 'kafka_actions-consumer-group')
        self.consumer = None

    def create_consumer(self):
        """Создает Kafka consumer"""
        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                auto_offset_reset='earliest',  # начинать с самого старого сообщения
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            logger.info(f"Kafka consumer created for topic: {self.topic}")
            return consumer
        except Exception as e:
            logger.error(f"Error creating Kafka consumer: {e}")
            return None

    @staticmethod
    def process_message(message):
        """Обрабатывает полученное сообщение"""
        try:
            logger.info("=" * 50)
            logger.info("📨 NEW MESSAGE RECEIVED")
            logger.info("=" * 50)
            logger.info(f"Topic: {message.topic}")
            logger.info(f"Partition: {message.partition}")
            logger.info(f"Offset: {message.offset}")
            logger.info(f"Key: {message.key}")
            logger.info("Message Data:")

            if isinstance(message.value, dict):
                for key, value in message.value.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {message.value}")

            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def start_consuming(self):
        """Запускает потребление сообщений"""
        logger.info("Starting Kafka Consumer Service...")
        logger.info(f"Bootstrap servers: {self.bootstrap_servers}")
        logger.info(f"Topic: {self.topic}")
        logger.info(f"Group ID: {self.group_id}")

        self.consumer = self.create_consumer()

        if not self.consumer:
            logger.error("Failed to create Kafka consumer. Exiting.")
            return

        try:
            logger.info("🎧 Listening for messages...")

            for message in self.consumer:
                self.process_message(message)

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("Kafka consumer closed")