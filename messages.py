from kafka import KafkaProducer, KafkaConsumer

# these are the basic functions to connecting to kakfa and publishing a message
# based on https://towardsdatascience.com/getting-started-with-apache-kafka-in-python-604b3250aa05

def publish_message(producer, topic, key, value):
    """
    publish message to a producer instance using a topic

    :param producer:  producer instance, an instance to KafkaProducer
    :param topic:  the topic to publish to, should already be created on Kafka side
    :param key: the key to publish to, incoded in UTF-8
    :param value: the value to publish, incoded in UTF-8
    :return: None
    """
    try:
        key_bytes = bytes(key, encoding="utf-8")
        value_bytes = bytes(value, encoding="utf-8")
        producer.send(topic, key=key_bytes, value=value_bytes)
        producer.flush()
        print('Message published successfuly.')
    except Exception as ex:
        print("Exception in publishing message.")
        print(str(ex))


def connect_kafka_producer():
    """
    connect to a kafka producer and return its instance

    :return: kafka producer instance
    """
    producer = None
    try:
        producer = KafkaProducer(bootstrap_servers = ["localhost:9092"], api_version = (0,10))
    except Exception as ex:
        print("Exception while connecting to kafka.")
        print(str(ex))
    finally:
        return producer


