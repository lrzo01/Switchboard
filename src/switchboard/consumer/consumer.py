import os
import json
import psycopg
import confluent_kafka as kafka
from switchboard.postgre import DarwinDatabase
from switchboard.processing import Processing
from switchboard.util import load_config_item, parse_pport_into_loadable_xml


class DarwinConsumer:
    def __init__(self, db: DarwinDatabase):
        self.config: dict[str, str | bool | None] = {
            "bootstrap.servers": load_config_item(
                "darwin", "kafka_bootstrap_server", str
            ),
            "sasl.username": os.getenv("CONSUMER_USERNAME"),
            "sasl.password": os.getenv("CONSUMER_PASSWORD"),
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "group.id": os.getenv("CONSUMER_GROUP"),
            "auto.offset.reset": "earliest",
            "enable.metrics.push": False,
        }

        self.status: str | None = None
        self.rebuilding_database = False

        if (
            self.config["bootstrap.servers"] == ""
            or self.config["sasl.username"] == ""
            or self.config["sasl.password"] == ""
            or self.config["group.id"] == ""
        ):
            raise ValueError("empty values in env for darwin feed")

        self.consumer = kafka.Consumer(self.config)
        self.topic = load_config_item("darwin", "topic", str)

        if self.topic == "":
            raise ValueError("no topic set")

        self.consumer.subscribe([self.topic])
        self.db = db
        self.processor = Processing(self.db)

    def _process_message(self, message: bytes | None):
        if message:
            decoded = message.decode("utf-8")
            obj = json.loads(decoded)
            xml_decoded: str = obj["bytes"]
            xml_parsed = parse_pport_into_loadable_xml(xml_decoded)
            self.processor.process(xml_parsed, self, "push_port")

    def start(self):
        try:
            while True:
                msg = self.consumer.poll(timeout=10)
                if self.status == "HBINIT" and self.rebuilding_database == False:
                    print("darwin has requested database rebuild")

                    self.rebuilding_database = True
                    self.processor.conn.close()

                    self.db.initalise_database()
                    self.processor.conn = psycopg.connect(
                        dbname=self.db.db_name,
                        user=self.db.user,
                        password=self.db.password,
                        host=self.db.host,
                        port=self.db.port,
                    )

                    self.processor.repopulate_database()

                    print("database has been rebuilt")
                    msg = None

                elif self.status == "HBOK" and self.rebuilding_database == True:
                    self.rebuilding_database = False

                if msg:
                    parsed_msg = msg.value()
                    self._process_message(parsed_msg)
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()
