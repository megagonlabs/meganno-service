import pydash
import pytest
from conftest import ValueStorage, app
from context import Service, log_test_case


@pytest.mark.order(6)
class TestAssignmentService:
    service = Service(app)

    def test_set_assignment(self):
        log_test_case("POST /assignments returns 200 with uuid of new subset")
        payload = self.service.get_base_payload()
        payload.update({"subset_uuid_list": ValueStorage.uuid_list})
        response = self.service.post("/assignments", json=payload)
        assert pydash.is_equal(response.status_code, 200)

    @pytest.mark.order(after="test_set_assignment")
    def test_get_assignment(self):
        log_test_case("GET /assignments return the correct assignment for user")
        payload = self.service.get_base_payload()
        response = self.service.get("/assignments", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        assignment = response.json
        assert len(assignment) > 0
        assn1 = assignment[0]
        assert pydash.is_equal(assn1["uuid_list"], ValueStorage.uuid_list)
