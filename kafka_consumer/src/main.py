import sys
import logging
from kafka_actions.consumer import KafkaMessageConsumer
from logging.handlers import RotatingFileHandler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler('kafka_consumer.log', maxBytes=1024 * 1024, backupCount=3,  encoding='utf-8')
    ]
)

def main():
    consumer_service = KafkaMessageConsumer()
    consumer_service.start_consuming()


if __name__ == "__main__":
    main()