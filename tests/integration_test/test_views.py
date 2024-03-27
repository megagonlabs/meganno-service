import json

import pydash
import pytest
from app.constants import MAX_QUERY_LIMIT
from conftest import TEST_USER_ID, ValueStorage, app
from context import Service, log_test_case
from result import VIEWS


@pytest.mark.order(5)
class TestViewsService():
    service = Service(app)

    def log_test_case(self, key, description):
        self.test_cases[key] = {"description": description, "status": False}

    def update_test_case(self, key, status=True):
        self.test_cases[key]["status"] = status
    
    def test_get_view_record(self):
        payload = self.service.get_base_payload()
        uuid_list = [ValueStorage.uuid_for_post_annotations]

        test_case = VIEWS["TEST_VIEW_RECORD_1"]
        # 'uuid' is dynamic; add to result
        for i, _ in enumerate(uuid_list):
            test_case[i]['uuid'] = uuid_list[i]

        parameters = {
            "record_id": True,
            "uuid_list": uuid_list
        }
        log_test_case(
             "GET /view/record returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload.update(parameters)
        response = self.service.get("/view/record", json=payload)
        assert pydash.is_equal(response.status_code, 200)

        result = response.json
        assert pydash.is_equal(result, test_case)
        
    
    def test_get_view_record_empty_uuid_list(self):
        payload = self.service.get_base_payload()

        parameters = {
            "uuid_list": []
        }
        log_test_case(
             "GET /view/record returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload.update(parameters)
        response = self.service.get("/view/record", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        result = response.json
        assert pydash.is_equal(result, [])


    def test_get_view_annotation(self):
        payload = self.service.get_base_payload()
        uuid_list = [ValueStorage.uuid_for_post_annotations]

        test_case = VIEWS["TEST_VIEW_ANNOTATION_1"]
        # 'uuid' is dynamic; add to result
        # also add annotator
        for i, _ in enumerate(uuid_list):
            test_case[i]['uuid'] = uuid_list[i]
            test_case[i]['annotation_list'][0]['annotator'] = TEST_USER_ID

        parameters = {
            "uuid_list": uuid_list
        }
        log_test_case(
             "GET /view/annotation returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload.update(parameters)
        response = self.service.get("/view/annotation", json=payload)
        assert pydash.is_equal(response.status_code, 200)

        result = response.json
        assert pydash.is_equal(result, test_case)
    

    def test_get_view_annotation_with_params(self):
        payload = self.service.get_base_payload()
        uuid_list = [ValueStorage.uuid_for_post_annotations]

        test_case = VIEWS["TEST_VIEW_ANNOTATION_2"]
        # 'uuid' is dynamic; add to result
        # also add annotator
        for i, _ in enumerate(uuid_list):
            test_case[i]['uuid'] = uuid_list[i]
            test_case[i]['annotation_list'][0]['annotator'] = TEST_USER_ID

        parameters = {
            "uuid_list": uuid_list, 
            "label_names": ["sentiment"],
            "label_meta_names": ["conf_score"],
            "annotator_list": [TEST_USER_ID]
        }
        log_test_case(
             "GET /view/annotation returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload.update(parameters)
        response = self.service.get("/view/annotation", json=payload)
        assert pydash.is_equal(response.status_code, 200)

        result = response.json
        assert pydash.is_equal(result, test_case)
        

    def test_get_view_verifications(self):
        payload = self.service.get_base_payload()
        response = self.service.get("/data/search", json=payload)
        uuid_list = response.json
        uuid_list = uuid_list[:3]

        test_case = VIEWS["TEST_VIEW_VERIFICATIONS_1"]
        # 'uuid' is dynamic; add to result
        for i, _ in enumerate(uuid_list):
            test_case[i]['uuid'] = uuid_list[i]

        parameters = {
            "uuid_list": uuid_list,
            "label_name": "uvw",
            "label_level": "record",
            "annotator": TEST_USER_ID,
            "verifier_filter": [TEST_USER_ID],
            "status_filter": "CORRECTS"
        }
        log_test_case(
             "GET /view/verifications returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload.update(parameters)
        response = self.service.get("/view/verifications", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        result = response.json
        assert pydash.is_equal(result, test_case)
        

    def test_get_view_verifications_with_malformed_payload(self):
        payload = self.service.get_base_payload()
        response = self.service.get("/data/search", json=payload)
        uuid_list = response.json
        uuid_list = uuid_list[:3]

        test_case = VIEWS["TEST_VIEW_VERIFICATIONS_1"]
        # 'uuid' is dynamic; add to result
        for i, _ in enumerate(uuid_list):
            test_case[i]['uuid'] = uuid_list[i]

        parameters = {
            "uuid_list": uuid_list,
            "label_name": "uvw",
            "label_level": "record",
            "annotator": TEST_USER_ID,
            "verifier_filter": [TEST_USER_ID],
            "status_filter": "FAILURE"
        }
        log_test_case(
             "GET /view/verifications returns 422 with parameters: {}".format(json.dumps(parameters))
        )
        payload.update(parameters)
        response = self.service.get("/view/verifications", json=payload)
        assert pydash.is_equal(response.status_code, 422)
        