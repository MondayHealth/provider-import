from collections import OrderedDict

from sqlalchemy.orm import Session

from provider.models.providers import Provider


class MungerPlugin:
    """ Fed to munger, instantiated once, with a method thats run every row """

    def __init__(self, session: Session, debug: bool):
        self._session: Session = session
        self._debug: bool = debug

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raise NotImplementedError

    def pre_process(self) -> None:
        pass

    def post_process(self) -> None:
        pass
