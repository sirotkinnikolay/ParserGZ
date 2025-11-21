import  logging
import sys
import os
from fastapi import FastAPI, HTTPException
from kafka.errors import KafkaError
from dotenv import load_dotenv
from  kafka_actions.producer import get_kafka_producer
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler('api_gateway.log', maxBytes=1024 * 1024, backupCount=3,  encoding='utf-8')
    ]
)

load_dotenv()

KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'topic_1')

app = FastAPI(
    title="API Gateway",
    description="API для входа в приложение.",
    version="1.0.0")


@app.get("/health")
async def health():
    """Health check endpoint"""
    producer = get_kafka_producer()
    kafka_status = "connected" if producer else "disconnected"

    return {
        "status": "healthy",
        "service": "api_gateway",
        "kafka_actions": kafka_status
    }


@app.get("/gateway/{action_name}")
async def send_to_kafka(action_name: str):
    """
    Принимает GET запрос и отправляет сообщение в Kafka topic_1
    """
    message = {"action": action_name}
    producer = get_kafka_producer()

    if not producer:
        raise HTTPException(
            status_code=500,
            detail="Kafka producer is not available"
        )

    try:
        # Отправляем сообщение в Kafka
        future = producer.send(
            topic=KAFKA_TOPIC,
            key=action_name,
            value=message
        )

        # Ждем подтверждения от Kafka
        record_metadata = future.get(timeout=10)

        return {
            "status": "success",
            "message": f"Action '{action_name}' sent to Kafka",
            "kafka_info": {
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset
            },
            "data": message
        }

    except KafkaError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kafka error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
    finally:
        producer.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)