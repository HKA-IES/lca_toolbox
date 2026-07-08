# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import pytest

# import your own module
from lcatoolbox import get_exchange
from setup_bw_project import setup_brightway, imported_activities

class TestUtils:

    def test_get_exchange(self, imported_activities):
        activities = imported_activities

        exchange_expected = [exc for exc in activities[0].exchanges()][0]

        exc_id = exchange_expected.id

        exchange_actual = get_exchange(exc_id)

        assert exchange_actual == exchange_expected

    def test_get_exchange_bad_id(self):
        with pytest.raises(ValueError):
            _ = get_exchange(9223372036854775807) # max value for int64
