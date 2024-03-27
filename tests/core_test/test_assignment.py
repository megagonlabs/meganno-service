import json
import unittest

import pytest
from conftest import TestCore, ValueStorage


@pytest.mark.order(5)
class TestAssignmentCore(TestCore):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sample_uuid_list1 = cls.project.search(limit=10)
        cls.sample_uuid_list2 = cls.project.search(limit=10, skip=10)

        cls.assignment_obj = cls.project.get_assignment_obj()
        cls.assigned_by = "TEST_DISPATCHER"
        cls.assigned_to = "TEST_ANNOTATOR"

    def test_set_assignment(self):
        result1 = self.assignment_obj.set_assignment(
            subset=TestAssignmentCore.sample_uuid_list1,
            annotator=TestAssignmentCore.assigned_to,
            assigned_by=TestAssignmentCore.assigned_by,
        )
        self.assertIsInstance(result1["uuid"], str)

        result2 = self.assignment_obj.set_assignment(
            subset=TestAssignmentCore.sample_uuid_list2,
            annotator=TestAssignmentCore.assigned_to,
            assigned_by=TestAssignmentCore.assigned_by,
        )
        self.assertIsInstance(result2["uuid"], str)

    @pytest.mark.order(after="test_set_assignment")
    def test_get_assignment(self):
        result_all = self.assignment_obj.get_assignment(
            TestAssignmentCore.assigned_to, latest_only=False
        )
        self.assertEqual(
            result_all[0]["data_uuid_list"], TestAssignmentCore.sample_uuid_list2
        )
        self.assertEqual(
            result_all[1]["data_uuid_list"], TestAssignmentCore.sample_uuid_list1
        )

        result_latest = self.assignment_obj.get_assignment(
            TestAssignmentCore.assigned_to, latest_only=True
        )
        self.assertEqual(
            result_latest[0]["data_uuid_list"], TestAssignmentCore.sample_uuid_list2
        )


if __name__ == "__main__":
    unittest.main()
