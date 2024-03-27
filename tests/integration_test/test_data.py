import json

import pydash
import pytest
from conftest import app
from context import Service, log_test_case


@pytest.mark.order(3)
class TestDataService:
    service = Service(app)

    def test_search_record_limit(self):
        parameters = {
            "limit": 3,
            "skip": 0,
        }
        log_test_case(
            "GET /data/search returns 200 with parameters: {}".format(
                json.dumps(parameters)
            )
        )
        payload = self.service.get_base_payload()
        payload.update(parameters)
        response = self.service.get("/data/search", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        result = response.json
        assert type(result) is list
        assert pydash.is_equal(len(result), 3)

    def test_search_record_keyword(self):
        parameters = {
            "keyword": "history"
        }
        log_test_case(
            "GET /data/search returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload = self.service.get_base_payload()
        payload.update(parameters)
        response = self.service.get("/data/search", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        result = response.json
        assert type(result) is list
        assert pydash.is_equal(len(result), 5)
        

    def test_search_record_regex(self):
        parameters = {
            "regex": "^cr.*s is.*$"
        }
        log_test_case(
            "GET /data/search returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload = self.service.get_base_payload()
        payload.update(parameters)
        response = self.service.get("/data/search", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        result = response.json
        assert type(result) is list
        assert pydash.is_equal(len(result), 2)
        

    def test_search_record_ann_list(self):
        parameters = {
            "annotator_list": []
        }
        log_test_case(
            "GET /data/search returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload = self.service.get_base_payload()
        payload.update(parameters)
        response = self.service.get("/data/search", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        result = response.json
        assert type(result) is list
        assert pydash.is_equal(result, [])
        
    
    def test_search_record_conditions(self):
        parameters = {
            "record_metadata_condition": {
                "name": "xyz",
                "operator": "exists",
                "value": None
            },
            "label_condition": {
                "name": "uvw",
                "operator": "==",
                "value": 0.2
            },
            "label_metadata_condition": {
                "label_name": "uvw",
                "name": "qwerty",
                "operator": ">",
                "value": 0.5
            },
            "verification_condition": {
                "label_name": "uvw",
                "search_mode": "ALL" 
            },
        }
        log_test_case(
            "GET /data/search returns 200 with parameters: {}".format(json.dumps(parameters))
        )
        payload = self.service.get_base_payload()
        payload.update(parameters)
        response = self.service.get("/data/search", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        result = response.json
        assert type(result) is list
        assert pydash.is_equal(result, [])
        

    def test_search_record_conditions_fail(self):
        parameters = {
            "record_metadata_condition": {
                "name": "xyz",
                "operator": "exists",
                "value": None
            },
            "label_condition": {
                "name": "uvw",
                "operator": "==",
                "value": 0.2
            },
            "label_metadata_condition": {
                "label_name": "uvw",
                "name": "qwerty",
                "operator": ">",
                "value": 0.5
            },
            "verification_condition": {
                "label_name": "uvw",
                "search_mode": "RANDOM" 
            },
        }
        log_test_case(
            "GET /data/search returns error with parameters: {}".format(json.dumps(parameters))
        )
        payload = self.service.get_base_payload()
        payload.update(parameters)
        response = self.service.get("/data/search", json=payload)
        assert pydash.is_equal(response.status_code, 422)
        
