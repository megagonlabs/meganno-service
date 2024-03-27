import json

import pydash
import pytest
from conftest import ValueStorage, app
from context import Service, log_test_case


@pytest.mark.order(2)
class TestSchemaService:
    service = Service(app)

    def test_set_schemas(self):
        log_test_case(
            "POST /schemas returns 200 with {}".format(
                json.dumps(ValueStorage.schemas)
            ),
        )
        payload = self.service.get_base_payload()
        payload.update({"schemas": ValueStorage.schemas})
        response = self.service.post("/schemas", json=payload)
        assert pydash.is_equal(response.status_code, 200)

    def test_get_schemas_with_false_active(self):
        log_test_case("GET /schemas with {'active': 'False'} returns empty list")
        payload = self.service.get_base_payload()
        payload.update({"active": False})
        response = self.service.get("/schemas", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        assert len(response.json) == 0

    @pytest.mark.order(after="test_set_schemas")
    def test_get_active_schemas(self):
        log_test_case(
            "GET /schemas with {'active': 'True'} returns the correct active schemas",
        )
        payload = self.service.get_base_payload()
        payload.update({"active": True})
        response = self.service.get("/schemas", json=payload)
        assert pydash.is_equal(response.status_code, 200)
        active_schemas = response.json
        assert len(active_schemas) > 0
        schema = active_schemas[0]
        assert schema["active"]
        assert pydash.is_equal(schema["schemas"], ValueStorage.schemas)

    def test_set_schema_with_invalid_schema(self):
        log_test_case("POST /schemas with invalid schema")
        # subcase 'level'
        payload = self.service.get_base_payload()
        payload.update({"schemas": pydash.clone_deep(ValueStorage.schemas)})
        pydash.set_(payload, "schemas.label_schema.0.level", "TRIGGER_ERROR")
        response = self.service.post("/schemas", json=payload)
        # invalid schema level: 422 json validation error
        assert pydash.is_equal(response.status_code, 422)
        # subcase 'options'
        payload = self.service.get_base_payload()
        payload.update({"schemas": pydash.clone_deep(ValueStorage.schemas)})
        pydash.set_(payload, "schemas.label_schema.0.options", [])
        response = self.service.post("/schemas", json=payload)
        # empty label options: 422 json validation error
        assert pydash.is_equal(response.status_code, 422)
        # subcase 'options'
        payload = self.service.get_base_payload()
        payload.update({"schemas": pydash.clone_deep(ValueStorage.schemas)})
        pydash.set_(payload, "schemas.label_schema.0.options.0.value", "false")
        response = self.service.post("/schemas", json=payload)
        # duplicate label option value: 400 custom validation error
        assert pydash.is_equal(response.status_code, 400)
