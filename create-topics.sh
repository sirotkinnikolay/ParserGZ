#!/bin/bash
echo "Creating Kafka topics..."

topics=(
  "topic_1:3:1"
  "topic_2:3:1"
  "topic_3:3:1"
  "topic_4:1:1"
)

for topic in "${topics[@]}"; do
  IFS=':' read -r name partitions replication <<< "$topic"
  kafka_actions-topics --bootstrap-server localhost:9092 \
    --create \
    --topic "$name" \
    --partitions "$partitions" \
    --replication-factor "$replication"

  echo "Created topic: $name"
done

echo "All topics created!"