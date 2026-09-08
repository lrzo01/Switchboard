from psycopg import sql
import os
import psycopg


class DarwinDatabase:
    def __init__(self) -> None:
        self.db_name = os.getenv("DB_NAME", "darwin_database")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.cursor = None
        self.initalise_database()

    def initalise_database(self) -> None:
        conn: psycopg.Connection

        with psycopg.connect(
            dbname="postgres",
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            autocommit=True,
        ) as conn:
            cursor: psycopg.Cursor
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid();
                """,
                    (self.db_name,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(
                        sql.Identifier(self.db_name)
                    )
                )
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name))
                )

        schema_path = os.path.join(os.path.dirname(__file__), "..", "build.sql")
        if not os.path.exists(schema_path):
            schema_path = "src/switchboard/build.sql"

        with psycopg.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            autocommit=True,
        ) as conn:
            cursor: psycopg.Cursor
            with conn.cursor() as cursor:
                cursor.execute(open(schema_path, "r").read())  # type: ignore
            conn.close()
