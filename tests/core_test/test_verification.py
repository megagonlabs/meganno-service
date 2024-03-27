import json
import unittest
from tarfile import RECORDSIZE

import pytest
from app.core.subset import Subset
from conftest import TestCore, ValueStorage


@pytest.mark.order(5)
class TestVerificationCore(TestCore):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sample_uuid_list = cls.project.search(limit=10)
        cls.record_uuid_true = sample_uuid_list[0]
        cls.record_uuid_false = sample_uuid_list[1]
        cls.record_uuid_double_label = sample_uuid_list[2]
        cls.record_label_true = ValueStorage.record_label_true
        cls.record_label_false = ValueStorage.record_label_false
        cls.record_label2_true = ValueStorage.record_label2_true
        cls.record_label2_false = ValueStorage.record_label2_false

        cls.annotator = "TEST_ANNOTATOR_TO_VERIFY"
        cls.verified_by = "TEST_VERIFIER"

    def helper_set_annotation(self, record_uuid, label):
        l = self.project.update_label(
            record_uuid=record_uuid, annotator=self.annotator, **label
        )
        self.project.update_annotation_with_labels(
            label_list=[l],
            annotator=self.annotator,
            record_uuid=record_uuid,
        )

    def test_set_verification(self):
        # set annotation
        self.helper_set_annotation(self.record_uuid_true, self.record_label_true)
        # confirms
        label = self.record_label_true
        result_confirms = self.project.verify(
            record_uuid=self.record_uuid_true,
            annotator_id=self.annotator,
            verified_by=self.verified_by,
            labels=[label],
            label_level=label["label_level"],
            label_name=label["label_name"],
        )
        self.assertIsInstance(result_confirms["verification_uuid"], str)

        # temp
        # result_updates = self.project.verify(
        #     record_uuid=self.record_uuid_true,
        #     annotator_id=self.annotator,
        #     verified_by=self.verified_by,
        #     labels=[self.record_label_false],
        #     label_level=label["label_level"],
        #     label_name=label["label_name"],
        # )
        # self.assertIsInstance(result_updates["verification_uuid"], str)
        # self.assertEqual(
        #     result_updates["verification_uuid"], result_confirms["verification_uuid"]
        # )

        # set annotation
        self.helper_set_annotation(self.record_uuid_false, self.record_label_false)
        # corrects
        label = self.record_label_true
        result_corrects = self.project.verify(
            record_uuid=self.record_uuid_false,
            annotator_id=self.annotator,
            verified_by=self.verified_by,
            labels=[label],
            label_level=label["label_level"],
            label_name=label["label_name"],
        )
        self.assertIsInstance(result_corrects["verification_uuid"], str)
        # result_empty = self.project.verify(
        #     record_uuid=self.record_uuid_false,
        #     annotator_id=self.annotator,
        #     verified_by=self.verified_by,
        #     labels=[],
        #     label_level=label["label_level"],
        #     label_name=label["label_name"],
        # )
        # temp set with empty list

    @pytest.mark.order(after="test_set_verification")
    def test_get_verfication(self):
        label_name = self.record_label_true["label_name"]
        label_level = "record"
        s_confirms = Subset(self.project, [self.record_uuid_true])
        label = self.record_label_false
        result = s_confirms.get_view_verification(
            label_level=label_level,
            label_name=label_name,
            annotator=self.annotator,
        )
        self.assertEqual(
            result[0]["verification_list"][0]["verification_status"], "CONFIRMS"
        )

        s_corrects = Subset(self.project, [self.record_uuid_false])

        result = s_corrects.get_view_verification(
            label_level=label_level,
            label_name=label_name,
            annotator=self.annotator,
        )
        self.assertEqual(
            result[0]["verification_list"][0]["verification_status"], "CORRECTS"
        )

    @pytest.mark.order(after="test_get_verfication")
    def test_set_second_label(self):
        # test cases with more than one label
        # l1 true, l2 false-> true correction

        # set annotation
        self.helper_set_annotation(
            self.record_uuid_double_label, self.record_label_true
        )
        self.helper_set_annotation(
            self.record_uuid_double_label, self.record_label2_false
        )
        # verify
        label = self.record_label2_true
        result_corrects = self.project.verify(
            record_uuid=self.record_uuid_double_label,
            annotator_id=self.annotator,
            verified_by=self.verified_by,
            labels=[label],
            label_level=label["label_level"],
            label_name=label["label_name"],
        )
        # test l2 correct status
        s_corrects = Subset(self.project, [self.record_uuid_double_label])
        label_name = self.record_label2_true["label_name"]
        label_level = "record"
        result = s_corrects.get_view_verification(
            label_level=label_level, label_name=label_name, annotator=self.annotator
        )
        self.assertEqual(
            result[0]["verification_list"][0]["verification_status"], "CORRECTS"
        )

    def test_get_verification_with_metadata(self):
        pass


if __name__ == "__main__":
    unittest.main()
