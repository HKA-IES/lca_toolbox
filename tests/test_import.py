# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules

# import your own module
from lcatoolbox import import_foreground
from setup_bw_project import *

class TestImport:
    FILE_PATH = "tests/test_import_foreground.ods"

    def test_import_foreground(self):
        activities = import_foreground(self.FILE_PATH)

        # Number of activities
        assert len(activities) == 2

        # Activities content
        assert activities[0]["name"] == "fruit_salad"
        assert activities[0]["unit"] == "item(s)"
        assert activities[0]["location"] == "DE"
        assert activities[1]["name"] == "juice"
        assert activities[1]["unit"] == "liter"
        assert activities[1]["location"] == "GLO"
