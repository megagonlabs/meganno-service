import json
import unittest

import pytest
from conftest import TestCore, ValueStorage


@pytest.mark.order(6)
class TestExportCore(TestCore):
    def test_export(self):
        result = self.project.export_data()
        pass
