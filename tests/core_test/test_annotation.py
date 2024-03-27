import unittest

import pytest
from app.constants import MAX_QUERY_LIMIT
from app.core.subset import Subset
from conftest import TestCore, ValueStorage


@pytest.mark.order(3)
class TestAnnotationCore(TestCore):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sample_uuid_list = []
        cls.label_list = []
        cls.annotator = "TEST_ANNOTATOR"
        cls.metadata_list = [
            {"metadata_name": "length", "metadata_value": 10},
            {"metadata_name": "confidence", "metadata_value": 0.1},
            {"metadata_name": "comment", "metadata_value": "test string"},
        ]

    @classmethod
    def tearDownClass(self):
        pass

    def test_annotation_get_data(self):
        # check for proper data
        result = self.project.search(limit=MAX_QUERY_LIMIT)
        self.assertEqual(len(result), 1000)

        TestAnnotationCore.sample_uuid_list = result[:10]

    @pytest.mark.order(after="test_annotation_get_data")
    def test_get_empty_annotation(self):
        s = Subset(self.project, TestAnnotationCore.sample_uuid_list)
        result = s.get_view_annotation(annotator_list=None)
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]["annotation_list"], [])

    @pytest.mark.order(after="test_get_empty_annotation")
    def test_set_annotation_record(self):
        record_label_true = ValueStorage.record_label_true
        record_label_false = ValueStorage.record_label_false
        for record_uuid in self.sample_uuid_list[0:5]:
            l = self.project.update_label(
                record_uuid=record_uuid, annotator=self.annotator, **record_label_true
            )
            result = self.project.update_annotation_with_labels(
                label_list=[l], annotator=self.annotator, record_uuid=record_uuid
            )
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0]["an_uuid"], str)
            self.label_list.append(l)

        for record_uuid in self.sample_uuid_list[5:9]:
            l = self.project.update_label(
                record_uuid=record_uuid, annotator=self.annotator, **record_label_false
            )
            result = self.project.update_annotation_with_labels(
                label_list=[l], annotator=self.annotator, record_uuid=record_uuid
            )
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0]["an_uuid"], str)
            self.label_list.append(l)

    @pytest.mark.order(after="test_set_annotation_record")
    def test_get_annotation_with_uuid_list(self):
        s = Subset(self.project, TestAnnotationCore.sample_uuid_list)
        result = s.get_view_annotation(annotator_list=None)
        self.assertEqual(len(result), 10)
        self.assertEqual(
            result[0]["annotation_list"][0]["labels_record"][0]
            | ValueStorage.record_label_true,
            result[0]["annotation_list"][0]["labels_record"][
                0
            ],  # diff: label_metadata_list
        )
        self.assertEqual(
            result[5]["annotation_list"][0]["labels_record"][0]
            | ValueStorage.record_label_false,
            result[5]["annotation_list"][0]["labels_record"][0],
        )

    @pytest.mark.order(after="test_set_annotation_record")
    def test_add_metadata_to_label(self):
        metadata_list = self.metadata_list
        test_label_uuid = self.label_list[0]

        result = self.project.add_metadata_to_label(
            label_uuid=test_label_uuid, metadata_list=metadata_list
        )
        self.assertEqual(len(result), len(metadata_list))
        # nonexisting label
        result = self.project.add_metadata_to_label(
            label_uuid="", metadata_list=metadata_list
        )
        self.assertEqual(len(result), 0)
        # empty metadata_list
        result = self.project.add_metadata_to_label(
            label_uuid=test_label_uuid, metadata_list=[]
        )
        self.assertEqual(len(result), 0)
        # duplicate metaname
        with self.assertRaises(ValueError):
            result = self.project.add_metadata_to_label(
                label_uuid=test_label_uuid, metadata_list=self.metadata_list
            )

        with self.assertRaises(ValueError):
            result = self.project.add_metadata_to_label(
                label_uuid=test_label_uuid, metadata_list=self.metadata_list[:1]
            )

    @pytest.mark.order(after="test_add_metadata_to_label")
    def test_add_label_with_metadata(self):

        s = Subset(self.project, TestAnnotationCore.sample_uuid_list)
        metadata_list = self.metadata_list

        # add with existing conflicting metadata
        record_uuid = self.sample_uuid_list[0]

        # assert label before update
        result = s.get_view_annotation(annotator_list=None)
        self.assertEqual(
            result[0]["annotation_list"][0]["labels_record"][0]
            | ValueStorage.record_label_true,
            result[0]["annotation_list"][0]["labels_record"][
                0
            ],  # diff: label_metadata_list
        )

        with self.assertRaises(ValueError):
            l = self.project.update_label(
                record_uuid=record_uuid,
                annotator=self.annotator,
                metadata_list=metadata_list,
                **ValueStorage.record_label_false,
            )

        # test content with get
        # assert label after update. should not change with
        # transaction roll-back.
        result = s.get_view_annotation(annotator_list=None)
        self.assertEqual(
            result[0]["annotation_list"][0]["labels_record"][0]
            | ValueStorage.record_label_true,
            result[0]["annotation_list"][0]["labels_record"][
                0
            ],  # diff: label_metadata_list
        )
        # add to record with label, no metadata
        record_uuid = self.sample_uuid_list[1]
        l = self.project.update_label(
            record_uuid=record_uuid,
            annotator=self.annotator,
            metadata_list=metadata_list,
            **ValueStorage.record_label_true,
        )
        self.assertIsInstance(l, str)
        # test content with get

        # add to fresh record
        record_uuid = self.sample_uuid_list[9]
        l = self.project.update_label(
            record_uuid=record_uuid,
            annotator=self.annotator,
            metadata_list=metadata_list,
            **ValueStorage.record_label_true,
        )

        self.assertIsInstance(l, str)

        # test content with get

    @pytest.mark.order(after="test_add_label_with_metadata")
    def test_zget_label_with_metadata(self):
        record_uuid = TestAnnotationCore.sample_uuid_list[1]
        s = Subset(self.project, [record_uuid])
        result = s.get_view_annotation(
            annotator_list=None,
            label_meta_names=[item["metadata_name"] for item in self.metadata_list],
        )
        expected_label_metadata_list = [
            {"name": "comment", "value": "test string"},
            {"name": "confidence", "value": 0.1},
            {"name": "length", "value": 10},
        ]
        self.assertDictContainsSubset(
            ValueStorage.record_label_true,
            result[0]["annotation_list"][0]["labels_record"][0],
        )
        self.assertEqual(
            sorted(expected_label_metadata_list, key=lambda x: x["name"]),
            sorted(
                result[0]["annotation_list"][0]["labels_record"][0][
                    "label_metadata_list"
                ],
                key=lambda x: x["name"],
            ),
        )

    @pytest.mark.order(after="test_zget_label_with_metadata")
    def test_set_spans(self):
        for record_uuid in self.sample_uuid_list[0:5]:
            result = self.project.annotate(
                labels={
                    "labels_span": [
                        ValueStorage.span_label_true1,
                        ValueStorage.span_label_true2,
                    ]
                },
                annotator=self.annotator,
                record_uuid=record_uuid,
            )

            self.assertIsInstance(result, str)
