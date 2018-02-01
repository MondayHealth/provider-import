""" For every raw address in the table, query the google maps API and record
its response """
import configparser
import json
import pprint
from typing import Mapping, List, Set
from urllib import request, parse

import progressbar
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

        print("Selecting", row_count, "rows...")
        rows: List[Address] = query.all()
        print("Complete")

        pbar = progressbar.ProgressBar(max_value=row_count, initial_value=0)
        i = 0
        no_results = set()
        queries = 0
        for row in rows:
            assert row.geocoding_api_response is None, "query is wrong"

            encoded_address = "&" + parse.urlencode({'address': row.raw})
            response = request.urlopen(self.URL + encoded_address)
            queries += 1
            result = json.loads(response.read())
            status = result['status']

            if status in self.STATUS_CODES:
                args = [row.id, row.geocoding_api_response, status,
                        self.STATUS_CODES[status]]
                raise Exception("{} {} : {} {}".format(*args))

            row.geocoding_api_response = result
            self._session.commit()

            i += 1
            pbar.update(i)

        print("Queries:", queries)
        pprint.pprint(no_results)

    @staticmethod
    def _zips_from_results(results: List[dict]) -> Set[int]:
        ret: Set[int] = set()
        for result in results:
            for component in result['address_components']:
                types = set(component['types'])
                if 'postal_code' in types:
                    ret.add(int(component['short_name']))
                    break
        return ret

    def extract_zipcodes(self) -> None:
        row_count = self._session.query(func.count(Address.id)).filter(
            and_(Address.geocoding_api_response.isnot(None)),
            Address.zip_code.is_(None)).scalar()
        query = self._session.query(Address) \
            .options(load_only('geocoding_api_response')) \
            .filter(and_(Address.geocoding_api_response.isnot(None),
                         Address.zip_code.is_(None)))

        print("Selecting", row_count, "rows...")
        rows: List[Address] = query.all()
        print("Complete")

        pbar = progressbar.ProgressBar(max_value=row_count, initial_value=0)
        i = 0
        for row in rows:
            assert row.geocoding_api_response is not None, "query is wrong"

            if 'results' not in row.geocoding_api_response:
                continue

            results = row.geocoding_api_response['results']

            if not results:
                continue

            if len(results) < 1:
                continue

            zips: Set[int] = self._zips_from_results(results)

            if len(zips) < 1:
                continue

            if len(zips) > 1:
                print(results)
                continue

            row.zip_code = list(zips)[0]

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
    # gms.scan()
    gms.extract_zipcodes()
    # gms.update()


if __name__ == '__main__':
    run_from_command_line()
