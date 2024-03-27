import json

import pydash
import pytest
from app.constants import MAX_QUERY_LIMIT
from conftest import TEST_USER_ID, ValueStorage, app
from context import Service, log_test_case
from result import ANNOTATION


@pytest.mark.order(4)
class TestAnnotationService:
    service = Service(app)

    def test_get_annotations(self):
        log_test_case("GET /annotations returns 200 with no parameter.")
        payload = self.service.get_base_payload()
        response = self.service.get("/annotations", json=payload)
        assert pydash.is_equal(response.status_code, 200)

    @pytest.mark.order(after="test_get_annotations_with_keyword_using_data")
    def test_get_annotations_with_uuid_list(self):
        log_test_case(
            f"GET /annotations with uuid_list parameters: [{ValueStorage.uuid_for_post_annotations}] returns correct result.",
        )
        payload = self.service.get_base_payload()
        payload.update({"uuid_list": [ValueStorage.uuid_for_post_annotations]})
        response = self.service.get("/annotations", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        assert pydash.is_equal(len(response.json), 1)
        assert pydash.is_equal(
            response.json[0]["uuid"], ValueStorage.uuid_for_post_annotations
        )

    def test_get_annotations_with_invalid_parameters(self):
        log_test_case("GET /annotations with invalid parameters returns 200.")
        # invalid 'limit'
        payload = self.service.get_base_payload()
        payload.update({"limit": -1})
        response = self.service.get("/annotations", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        # big 'limit'
        payload = self.service.get_base_payload()
        payload.update({"limit": 11111111111})
        response = self.service.get("/annotations", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        assert len(response.json) <= MAX_QUERY_LIMIT
        # invalid 'skip'
        payload = self.service.get_base_payload()
        payload.update({"skip": -1})
        response = self.service.get("/annotations", json=payload)
        assert pydash.is_equal(response.status_code, 200)

    @pytest.mark.order(before="test_post_annotations")
    def test_get_annotations_with_keyword_using_data(self):
        parameters = {"keyword": "criminal"}
        log_test_case(
            "GET /annotations using data with parameters: {}".format(
                json.dumps(parameters)
            ),
        )
        data_basepayload = self.service.get_base_payload()
        data_basepayload.update(parameters)
        data_response = self.service.get("/data/search", json=data_basepayload)
        assert pydash.is_equal(data_response.status_code, 200)

        annotatons_payload = self.service.get_base_payload()
        annotatons_payload.update({"uuid_list": data_response.json})
        annotations_response = self.service.get("/annotations", json=annotatons_payload)
        assert pydash.is_equal(annotations_response.status_code, 200)
        result = annotations_response.json
        for data in result:
            if ValueStorage.uuid_for_post_annotations is None:
                ValueStorage.uuid_for_post_annotations = data["uuid"]
            data.pop("uuid")
        assert pydash.is_equal(result, ANNOTATION["TEST_1"])

    def test_post_annotations(self):
        payload = self.service.get_base_payload()
        payload.update({"labels": ValueStorage.labels})
        target_uuid = ValueStorage.uuid_for_post_annotations
        assert target_uuid is not None
        log_test_case(
            "POST /annotations/{} with labels: {}".format(
                target_uuid, json.dumps(ValueStorage.labels)
            ),
        )
        response = self.service.post(
            "/annotations/{}".format(target_uuid), json=payload
        )
        assert pydash.is_equal(response.status_code, 200)

    @pytest.mark.order(after="test_post_annotations")
    def test_get_annotations_with_labels(self): 
        label_condition = ValueStorage.label_condition
        data_payload = self.service.get_base_payload()
        data_payload.update({"label_condition": label_condition})
        log_test_case(
            "GET /annotations from /data with label: {}".format(
                json.dumps(label_condition)
            ),
        )
        data_response = self.service.get("/data/search", json=data_payload)
        assert pydash.is_equal(data_response.status_code, 200)
        data_result = data_response.json
        # fetch annotations by uuid
        annotations_payload = self.service.get_base_payload()
        annotations_payload.update({"uuid_list": data_result})
        response = self.service.get("/annotations", json=annotations_payload)
        assert pydash.is_equal(response.status_code, 200)
        annotations_result = response.json
        annotations_result[0].pop("uuid")
        # remove annotator id
        for annotation in annotations_result[0]["annotation_list"]:
            annotation["annotator"] = TEST_USER_ID
        assert pydash.is_equal(annotations_result, ANNOTATION["TEST_4"])

    def test_get_annotations_with_invalid_labels(self):
        payload = self.service.get_base_payload()
        payload.update({"label": "abc"})
        log_test_case(
            "GET /annotations with invalid label '{}' returns 200.".format(
                json.dumps("abc")
            ),
        )
        response = self.service.get("/annotations", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        assert pydash.is_equal(response.json, [])
