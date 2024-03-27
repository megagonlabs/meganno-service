import json

import pydash
from app.constants import d7validate
from deepdiff import DeepDiff


class Schema:
    def __init__(self, project):
        self.project = project

    def get_values(self, active=True):
        q = []
        if active is not None:
            q.append("MATCH (s:Schema)-[r:SCHEMA_OF {active: $active}]")
        else:
            q.append("MATCH (s:Schema)-[r:SCHEMA_OF]")
        q.append(
            """
            -(p:Project {name: $project_name})
            return s.uuid as uuid, r.active as active, s.obj_str as obj_str,
            datetime(s.created_on).epochMillis as created_on
            ORDER BY created_on DESC
        """
        )
        return self.project.database.read_db(
            query="\n".join(q),
            args={"project_name": self.project.project_name, "active": active},
        )

    def __set_all_schemas_to_inactive(self):
        q = """
            MATCH (s:Schema)-[r:SCHEMA_OF]-(p:Project {name: $project_name})
            SET r.active = False
        """
        args = {"project_name": self.project.project_name}
        self.project.database.write_db(q, args=args)

    def set_values(self, schemas):
        """
        If schemas are different than the current active schemas,
        create an active one and deactivate the old one.
        """
        validation_errors = validate_schemas(schemas)
        if len(validation_errors) == 0:
            existing_active_schema = self.get_values(active=True)
            diff = DeepDiff(
                json.loads(pydash.get(existing_active_schema, "0.obj_str", "{}")),
                schemas,
                ignore_order=True,
            )
            if diff:
                self.__set_all_schemas_to_inactive()
                args = {
                    "project_name": self.project.project_name,
                    "obj_str": json.dumps(schemas),
                }
                # create new schema and set it to active
                q = """
                    CREATE (s:Schema) 
                    SET s.uuid=randomUUID(), s.obj_str=$obj_str, s.created_on=DateTime() 
                    WITH s MATCH (p:Project {name: $project_name})
                    WITH s,p MERGE (s)-[rel:SCHEMA_OF {active: True}]-(p)
                    RETURN s.uuid as uuid, s.obj_str as obj_str
                """
                result = self.project.database.write_db(q, args=args)
                if len(result) == 1:
                    return {
                        "uuid": result[0]["uuid"],
                        "schemas": json.loads(result[0]["obj_str"]),
                    }
                else:
                    return False
            return {
                "uuid": existing_active_schema[0]["uuid"],
                "schemas": json.loads(existing_active_schema[0]["obj_str"]),
            }
        return validation_errors


def validate_schemas(schemas):
    errors = []
    label_schema = schemas["label_schema"]
    unique_label_names = set()
    for label in label_schema:
        label_name = label["name"]
        if label_name in unique_label_names:
            errors.append(
                f"'{label_name}' appears more than once. Label name should be unique within the label schema."
            )
        unique_label_names.add(label_name)
        options = label["options"]
        unique_options = set()
        for opt in options:
            opt_value = opt["value"]
            if opt_value in unique_options:
                errors.append(
                    f"options for '{label_name}' can not have duplicate values."
                )
            unique_options.add(opt_value)
    return errors
