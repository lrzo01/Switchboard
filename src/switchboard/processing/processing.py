from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import psycopg

import switchboard.processing.pushport as PP
import switchboard.processing.reference as RP
import switchboard.processing.timetable as TP
from switchboard.postgre import DarwinDatabase
from switchboard.processing.util import populate

if TYPE_CHECKING:
    from switchboard.consumer.consumer import DarwinConsumer


class Processing:
    def __init__(self, db: DarwinDatabase) -> None:
        self.conn: psycopg.Connection = psycopg.connect(
            dbname=db.db_name,
            user=db.user,
            password=db.password,
            host=db.host,
            port=db.port,
        )
        self.populating = False

        self.queue: list[tuple[list[ET.Element], DarwinConsumer | None, str]] = []
        self.repopulate_database()

    def repopulate_database(self) -> None:
        self.populating = True
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SET synchronous_commit = OFF;")
                cursor.execute("SET work_mem = '128MB';")
                cursor.execute("SET maintenance_work_mem = '256MB';")
            populate(self)
        finally:
            self.populating = False

        while self.queue:
            xml_list, consumer, source = self.queue.pop(0)
            self.process(xml_list, consumer, source)

    def process(
        self,
        xml: list[ET.Element],
        consumer: DarwinConsumer | None = None,
        source: str = "n/a",
    ) -> None:
        if source == "push_port" and self.populating:
            self.queue.append((xml, consumer, source))
            return

        try:
            for entry in xml:
                for elem in entry.iter():
                    tag = elem.tag.split("}")[-1]
                    if tag == "LocationRef":
                        RP.LocationRef(self.conn, elem)
                    elif tag == "TocRef":
                        RP.TocRef(self.conn, elem)
                    elif tag == "LateRunningReasons":
                        for r in elem:
                            RP.LateRunningReason(self.conn, r)
                    elif tag == "CancellationReasons":
                        for r in elem:
                            RP.CancellationReason(self.conn, r)
                    elif tag == "Via":
                        RP.Via(self.conn, elem)
                    elif tag == "CISSource":
                        RP.CISSource(self.conn, elem)
                    elif tag == "LoadingCategories":
                        for cat in elem:
                            RP.LoadingCategory(self.conn, cat)
                    elif tag == "Journey":
                        TP.Journey(self.conn, elem)
                    elif tag == "Association":
                        TP.Association(self.conn, elem)
                    elif tag == "FailureResp":
                        code = elem.attrib.get("code")
                        if code and consumer:
                            PP.FailureResp(self.conn, elem)
                            consumer.status = code
                    elif tag == "schedule":
                        PP.Schedule(self.conn, elem)
                    elif tag == "deactivated":
                        PP.Deactivated(self.conn, elem)
                    elif tag == "association":
                        PP.Association(self.conn, elem)
                    elif tag == "scheduleFormations":
                        PP.ScheduleFormations(self.conn, elem)
                    elif tag == "formationLoading":
                        PP.FormationLoading(self.conn, elem)
                    elif tag == "serviceLoading":
                        PP.ServiceLoading(self.conn, elem)
                    elif tag == "TS":
                        PP.TS(self.conn, elem)
                    elif tag in ("TrainOrder", "trainOrder"):
                        PP.TrainOrder(self.conn, elem)
                    elif tag == "OW":
                        PP.OW(self.conn, elem)
                    elif tag in ("trainAlert", "AdhocAlert"):
                        PP.TrainAlert(self.conn, elem)
                    elif tag == "trackingID":
                        PP.TrackingID(self.conn, elem)
                    elif tag == "alarm":
                        PP.Alarm(self.conn, elem)
                    elif tag == "stationInformation":
                        PP.StationInformation(self.conn, elem)

            self.conn.commit()

        except Exception:
            self.conn.rollback()
            raise
