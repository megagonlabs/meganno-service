import json
import unittest

import pytest
from conftest import TestCore, ValueStorage


@pytest.mark.order(1)
class TestSchemaCore(TestCore):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema_obj = cls.project.get_schemas()

    @classmethod
    def tearDownClass(cls):
        pass
        # reset valid schema to active
        result = cls.schema_obj.set_values(ValueStorage.schema2)

    def test_set_schema(self):
        result = self.schema_obj.set_values(ValueStorage.schema1)

        self.assertIsNotNone(result["uuid"])
        self.assertEqual(result["schemas"], ValueStorage.schema1)
        # test invalid schema
        # result_invalid = self.schema_obj.set_values(ValueStorage.schema_invalid)

        # self.assertIsInstance(result_invalid, list)

        # TODO: raise error for invalid schema input

    @pytest.mark.order(after="test_set_schema")
    def test_get_schema(self):
        result = self.schema_obj.get_values(active=True)[0]

        self.assertIsNotNone(result["uuid"])
        self.assertEqual(json.loads(result["obj_str"]), ValueStorage.schema1)

    @pytest.mark.order(after="test_get_schema")
    def test_update_schema(self):
        result = self.schema_obj.set_values(ValueStorage.schema2)

        self.assertIsNotNone(result["uuid"])
        self.assertEqual(result["schemas"], ValueStorage.schema2)

    @pytest.mark.order(after="test_update_schema")
    def test_get_updated_schema(self):
        # get active schema
        result = self.schema_obj.get_values(active=True)[0]
        self.assertIsNotNone(result["uuid"])
        self.assertEqual(json.loads(result["obj_str"]), ValueStorage.schema2)
        # get inactive schema
        result_inactive = self.schema_obj.get_values(active=False)[0]
        self.assertIsNotNone(result["uuid"])
        self.assertEqual(json.loads(result_inactive["obj_str"]), ValueStorage.schema1)
        # get entire schema history
        result_hisotry = result_inactive = self.schema_obj.get_values(active=None)
        self.assertEqual(len(result_hisotry), 2)


if __name__ == "__main__":
    unittest.main()
