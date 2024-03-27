import pydash
import pytest
from conftest import app
from context import Service, log_test_case


@pytest.mark.order(5)
class TestReconciliationService:
    service = Service(app)

    def test_get_reconciliations(self):
        log_test_case("GET /reconciliations returns 422 with no parameter")
        payload = self.service.get_base_payload()
        response = self.service.get("/reconciliations", json=payload)
        assert pydash.is_equal(response.status_code, 422)

    def test_get_reconciliations_with_uuid_list(self):
        log_test_case("GET /reconciliations returns 200 with uuid_list")
        payload = self.service.get_base_payload()
        payload.update({"uuid_list": ["dummy-uuid"]})
        response = self.service.get("/reconciliations", json=payload)
        assert pydash.is_equal(response.status_code, 200)
