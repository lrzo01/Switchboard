from switchboard.postgre import DarwinDatabase
from switchboard.consumer import DarwinConsumer


def main() -> None:
    database = DarwinDatabase()

    consumer = DarwinConsumer(database)
    consumer.start()
