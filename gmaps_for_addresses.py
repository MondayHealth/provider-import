""" For every raw address in the table, query the google maps API and record
its response """
import configparser
import pprint
from concurrent.futures import Future, FIRST_COMPLETED, wait
from time import sleep
from typing import Mapping, List, Set, Union, MutableMapping
from urllib import parse

import progressbar
from requests import Response
from requests_futures.sessions import FuturesSession
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker, scoped_session, Session, load_only

from db_url import get_db_url
from provider.models.address import Address
# noinspection PyUnresolvedReferences
from provider.models.providers import Provider


class GoogleMapsScanner:
    ECHO_SQL: bool = False

    KEY: str = 'AIzaSyAjLhneW2pquw-e8kCaZ2BfJ3nW5-SgRKQ'

    URL: str = "https://maps.googleapis.com/maps/api/geocode/json?key=" + KEY

    REQUERY: bool = False

    MAX_REQUESTS: int = 25

    REQUEST_TIMEOUT: int = 5

    STATUS_CODES: Mapping[str, str] = {
        "OVER_QUERY_LIMIT": "you are over your quota.",
        "REQUEST_DENIED": "your request was denied.",
        "UNKNOWN_ERROR": "the request could not be processed due to a server "
                         "error. The request may succeed if you try again.",
    }

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=self.ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)
        self._Session.configure()
        self._session: Session = self._Session()

    def scan(self) -> None:
        row_count = self._session.query(func.count(Address.id)).filter(
            Address.geocoding_api_response.is_(None)).scalar()
        query = self._session.query(Address) \
            .options(load_only('raw')) \
            .filter(Address.geocoding_api_response.is_(None))

        print("Selecting", row_count, "rows to ask Google about...")
        rows: List[Address] = query.all()
        print("Complete")

        pbar = progressbar.ProgressBar(max_value=row_count, initial_value=0)
        i = 0
        no_results = set()
        queries = 0
        session: FuturesSession = FuturesSession(max_workers=self.MAX_REQUESTS)
        current_futures: Set[Future] = set()
        future_row_map: MutableMapping[Future, Address] = {}

        while len(rows) > 0:

            current_requests_in_flight = len(current_futures)

            for idx in range(1, self.MAX_REQUESTS - current_requests_in_flight):
                if len(rows) < 1:
                    break
                row = rows.pop()
                encoded_address = "&" + parse.urlencode({'address': row.raw})
                response: Future = session.get(self.URL + encoded_address)
                future_row_map[response] = row
                current_futures.add(response)
                queries += 1

            # Wait on the next future to finish
            done, current_futures = wait(current_futures,
                                         self.REQUEST_TIMEOUT,
                                         FIRST_COMPLETED)

            # For everything done, add it to the db!
            changes = False
            for future in done:
                row = future_row_map.pop(future)
                result: Response = future.result()
                data: dict = result.json()
                status = data['status']

                if status in self.STATUS_CODES:
                    if status == "OVER_QUERY_LIMIT":
                        print("Throttled")
                        sleep(2)
                    else:
                        continue

                row.geocoding_api_response = data

                api_results: dict = data.get("results", None)
                if api_results:
                    zip_code = self._zip_from_results(api_results)
                    if zip_code is not None:
                        row.zip_code = zip_code

                changes = True

                i += 1
                pbar.update(i)

            if changes:
                self._session.commit()

        print("Queries:", queries)
        pprint.pprint(no_results)

    @staticmethod
    def _zip_from_results(results: dict) -> Union[int, None]:
        if not results:
            return None

        if len(results) < 1:
            return None

        zips: Set[int] = set()
        for result in results:
            for component in result['address_components']:
                types = set(component['types'])
                if 'postal_code' in types:
                    try:
                        zips.add(int(component['short_name']))
                    except ValueError:
                        pprint.pprint(results)
                    break

        if len(zips) < 1:
            return None

        if len(zips) > 1:
            return None

        return list(zips)[0]

    def extract_zipcodes(self) -> None:
        row_count = self._session.query(func.count(Address.id)).filter(
            and_(Address.geocoding_api_response.isnot(None)),
            Address.zip_code.is_(None)).scalar()
        query = self._session.query(Address) \
            .options(load_only('geocoding_api_response')) \
            .filter(and_(Address.geocoding_api_response.isnot(None),
                         Address.zip_code.is_(None)))

        print("Selecting", row_count, "rows from which to extract zips...")
        rows: List[Address] = query.all()
        print("Complete")

        pbar = progressbar.ProgressBar(max_value=row_count, initial_value=0)
        i = 0
        for row in rows:
            assert row.geocoding_api_response is not None, "query is wrong"

            if 'results' not in row.geocoding_api_response:
                continue

            results = row.geocoding_api_response['results']
            zip_code = self._zip_from_results(results)

            if zip_code is not None:
                row.zip_code = zip_code

            if i % 1000:
                self._session.commit()

            i += 1
            pbar.update(i)

        self._session.commit()

    def update(self) -> None:
        print("Updating addresses.")
        self._session.execute("""
        UPDATE monday.address SET formatted = geocoding_api_response #>> '{
        results,0,formatted_address}'
        """)
        self._session.commit()
        print("Done")

        print("Updating points.")
        self._session.execute("""
        UPDATE monday.address SET point = st_geomfromtext('POINT(' ||
        (geocoding_api_response #>> '{results, 0, geometry, location, lng}') 
        || ' ' ||
        (geocoding_api_response #>> '{results, 0, geometry, location, lat}') 
        || ')', 4326)
        """)
        self._session.commit()
        print("Done")


def run_from_command_line() -> None:
    gms = GoogleMapsScanner()
    gms.scan()
    # gms.extract_zipcodes()
    gms.update()


if __name__ == '__main__':
    run_from_command_line()
