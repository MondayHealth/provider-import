import re

from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY


class NumericRangeArray(ARRAY):

    def bind_expression(self, bind_value):
        return cast(bind_value, self)

    def result_processor(self, dialect, col_type):
        super_rp = super().result_processor(dialect, col_type)

        def handle_raw_string(value):
            return value

        def process(value):
            if value is None:
                return None
            return super_rp(handle_raw_string(value))

        return process
