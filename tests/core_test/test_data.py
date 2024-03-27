import json
import unittest

import pytest
from app.constants import MAX_QUERY_LIMIT
from conftest import TestCore, ValueStorage


@pytest.mark.order(2)
class TestDataCore(TestCore):
    @classmethod
    def tearDownClass(cls):
        pass

    def test_data_get_schema(self):
        # check for proper schema
        result = self.project.get_schemas().get_values(active=True)[0]

        self.assertIsNotNone(result["uuid"])
        self.assertEqual(json.loads(result["obj_str"]), ValueStorage.schema2)

    @pytest.mark.order(after="test_data_get_schema")
    def test_import_csv(self):
        import_url = ValueStorage.import_url
        column_mapping = ValueStorage.import_column_mapping
        result = self.project.import_data(
            url=import_url, file_type="csv", column_mapping=column_mapping
        )
        self.assertEqual(result, 1000)

    @pytest.mark.order(after="test_import_csv")
    def test_import_df(self):
        df_dict = ValueStorage.import_df_dict
        result = self.project.import_data(
            file_type="df",
            column_mapping=ValueStorage.import_column_mapping,
            df_dict=df_dict,
        )
        self.assertEqual(result, 3)

    def test_invalid_input(self):
        pass

    @pytest.mark.order(after="test_import_df")
    def test_search_keyword(self):
        result = self.project.search(keyword="certificate")
        self.assertEqual(len(result), 3)

    @pytest.mark.order(after="test_import_df")
    def test_search_regex(self):
        regex = "^cr.*s is.*$"
        result = self.project.search(regex=regex)
        self.assertEqual(len(result), 2)

    @pytest.mark.order(after="test_import_df")
    def test_invalid_search(self):
        pass

    @pytest.mark.order(after="test_import_df")
    def test_search_verification(self):
        pass

    @pytest.mark.order(after="test_import_df")
    def test_import_with_record_metadata(self):
        pass

    @pytest.mark.order(after="test_import_df")
    def test_import_record_meta(self):
        cnt = 10
        data_uuid_list = self.project.search(keyword="", limit=cnt)

        record_metadata_list = [
            {"uuid": uuid, "value": idx} for idx, uuid in enumerate(data_uuid_list)
        ]
        result = self.project.batch_update_metadata(
            record_meta_name="test_record_meta", metadata_list=record_metadata_list
        )
        self.assertEqual(result, cnt)

    @pytest.mark.order(after="test_import_record_meta")
    def test_search_metadata(self):
        # search by record and label metadata
        pass

    def test_search_conflict(self):
        # TODO: test for span-level
        ### set conflicting data
        uuid_list = self.project.search(limit=20)
        # conflicts for label_name1
        record_uuid1 = uuid_list[10]

        self.project.annotate(
            labels={
                "labels_record": [
                    ValueStorage.record_label_true,
                ]
            },
            annotator="TEST_ANNOTATOR1",
            record_uuid=record_uuid1,
        )
        self.project.annotate(
            labels={
                "labels_record": [
                    ValueStorage.record_label_false,
                ]
            },
            annotator="TEST_ANNOTATOR2",
            record_uuid=record_uuid1,
        )
        self.project.annotate(
            labels={
                "labels_record": [
                    ValueStorage.record_label_true,
                ]
            },
            annotator="TEST_ANNOTATOR3",
            record_uuid=record_uuid1,
        )
        label_name1 = ValueStorage.record_label_false["label_name"]

        # conflicts for label_name2
        record_uuid2 = uuid_list[11]

        self.project.annotate(
            labels={
                "labels_record": [
                    ValueStorage.record_label2_true,
                ]
            },
            annotator="TEST_ANNOTATOR1",
            record_uuid=record_uuid2,
        )
        self.project.annotate(
            labels={
                "labels_record": [
                    ValueStorage.record_label2_false,
                ]
            },
            annotator="TEST_ANNOTATOR2",
            record_uuid=record_uuid2,
        )
        label_name2 = ValueStorage.record_label2_false["label_name"]
        ## Test
        # test label_name1, should not retrieve record_uuid2
        result = self.project.search(
            label_condition={"name": label_name1, "operator": "conflicts"},
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], record_uuid1)

        # test subset annotators, only return conflicts between annotator 1 & 3
        result = self.project.search(
            annotator_list=["TEST_ANNOTATOR1", "TEST_ANNOTATOR3"],
            label_condition={"name": label_name1, "operator": "conflicts"},
        )
        self.assertEqual(len(result), 0)

        result = self.project.search(
            label_condition={"name": label_name2, "operator": "conflicts"},
            verification_condition={
                "label_name": label_name1,
                "search_mode": "UNVERIFIED",
            },
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], record_uuid2)


if __name__ == "__main__":
    unittest.main()
