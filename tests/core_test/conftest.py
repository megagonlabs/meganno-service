import os
import secrets
import sys
import time
import unittest
import urllib.request

import docker


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


neo4j_container = None


def remove_container(container):
    try:
        container.remove(force=True, v=True)
        print(f"Container {container.id} removed")
    except Exception:
        pass


try:
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../api"))
    )
    from app.core.database import Database
    from app.core.project import Project

    if "TEST_NEO4J_BOLT_PORT" in os.environ and "TEST_NEO4J_PASSWORD" in os.environ:
        # use existing db for testing
        try:
            print(
                f"Testing with local instance at port {os.environ['TEST_NEO4J_BOLT_PORT']}"
            )
            CORE_DATABASE = Database(
                uri=f"bolt://localhost:{os.environ['TEST_NEO4J_BOLT_PORT']}",
                username="neo4j",
                password=os.environ["TEST_NEO4J_PASSWORD"],
            )
            CORE_PROJECT = Project(database=CORE_DATABASE, project_name="core_test")
        except Exception as ex:
            print("Failed to connect to database", ex)

    else:
        client = docker.from_env()
        MEGANNO_NEO4J_PASSWORD = secrets.token_hex(16)
        neo4j_container = client.containers.run(
            "neo4j:4.4.27-community",
            detach=True,
            ports={7473: 17473, 7474: 17474, 7687: 17687},
            environment={
                "NEO4J_AUTH": f"neo4j/{MEGANNO_NEO4J_PASSWORD}",
                "NEO4JLABS_PLUGINS": '["apoc","graph-data-science"]',
                "NEO4J_dbms_security_procedures_allowlist": "gds.*,apoc.*",
                "NEO4J_dbms_security_procedures_unrestricted": "gds.*,apoc.* ",
            },
            auto_remove=True,
        )
        print(f"Container {neo4j_container.id} started")

        while True:
            try:
                time.sleep(10)
                status_code = urllib.request.urlopen("http://localhost:17474").getcode()
                if status_code == 200:
                    break
            except Exception:
                pass

        CORE_DATABASE = Database(
            uri=f"bolt://localhost:17687",
            username="neo4j",
            password=MEGANNO_NEO4J_PASSWORD,
        )
        CORE_PROJECT = Project(database=CORE_DATABASE, project_name="core_test")

    def pytest_sessionstart(session):
        CORE_DATABASE.write_db(
            "Match (n)  WHERE NOT 'Project' in labels(n) DETACH DELETE(n)", {}
        )
        print(f"database reset before session.")

    def pytest_sessionfinish(session):
        remove_container(neo4j_container)

    class TestCore(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.project = CORE_PROJECT

        @classmethod
        def tearDownClass(cls):
            pass

        def setup_method(self, method):
            print(f"\n{type(self).__name__}:{method.__name__}")

    def pytest_addoption(parser):
        parser.addoption("--name", action="store", default="default name")

    class ValueStorage:
        uuid_for_post_annotations = None
        schema1 = {
            "label_schema": [
                {
                    "name": "pair_validation",
                    "level": "record",
                    "options": [
                        {"value": "true", "text": "Correct pair"},
                        {"value": "false", "text": "Incorrect pair"},
                        {"value": "unresolved", "text": "Inconclusive pair"},
                    ],
                }
            ]
        }
        schema2 = {
            "label_schema": [
                {
                    "name": "pair_validation",
                    "level": "record",
                    "options": [
                        {"value": "true", "text": "Correct pair"},
                        {"value": "false", "text": "Incorrect pair"},
                        {"value": "unresolved", "text": "Inconclusive pair"},
                    ],
                },
                {
                    "name": "related_span",
                    "level": "span",
                    "options": [
                        {"value": "true", "text": "Spans related to correct pairs"},
                        {"value": "false", "text": "Spans related to incorrect pair"},
                        {"value": "others", "text": "Other related spans"},
                    ],
                },
            ]
        }
        schema_invalid = {
            "label_schema": [
                {
                    "name": "pair_validation",
                    # "level": "record",
                    "options": [
                        {"value": "true", "text": "Correct pair"},
                        {"value": "false", "text": "Incorrect pair"},
                        {"value": "unresolved", "text": "Inconclusive pair"},
                    ],
                }
            ]
        }
        import_url = "https://drive.google.com/uc?id=1w2RcWKYnF-Gj9jwJgh8Ju_uyfnyoghHN&export=download"

        import_column_mapping = {"id": "sent_id", "content": "content"}
        import_df_dict = [  # first 3 items of the dataset in the url
            {
                "sent_id": 1,
                "content": "background_screening,criminal history,criminal history is a ,criminal history is a background_screening",
            },
            {
                "sent_id": 2,
                "content": "background_screening,fingerprints,fingerprints is a ,fingerprints is a background_screening",
            },
            {
                "sent_id": 3,
                "content": "background_screening,employment,employment is a ,employment is a background_screening",
            },
        ]

        record_label_true = {
            "label_name": "pair_validation",
            "label_value": ["true"],
            "label_level": "record",
        }
        record_label_false = {
            "label_name": "pair_validation",
            "label_value": ["false"],
            "label_level": "record",
        }

        record_label2_true = {
            "label_name": "pair_validation2",
            "label_value": ["true"],
            "label_level": "record",
        }
        record_label2_false = {
            "label_name": "pair_validation2",
            "label_value": ["false"],
            "label_level": "record",
        }

        span_label_true1 = {
            "label_name": "related_span",
            "label_value": ["true"],
            "label_level": "span",
            "start_idx": 0,
            "end_idx": 3,
        }

        span_label_true2 = {
            "label_name": "related_span",
            "label_value": ["true"],
            "label_level": "span",
            "start_idx": 3,
            "end_idx": 5,
        }
        span_label_false1 = {
            "label_name": "related_span",
            "label_value": ["false"],
            "label_level": "span",
            "start_idx": 0,
            "end_idx": 3,
        }
        span_label_false3 = {
            "label_name": "related_span",
            "label_value": ["false"],
            "label_level": "span",
            "start_idx": 2,
            "end_idx": 4,
        }

except Exception as ex:
    remove_container(neo4j_container)
    raise ex
except KeyboardInterrupt:
    print(
        f"{bcolors.WARNING} Deleting container due to forced termination{bcolors.ENDC}"
    )
    remove_container(neo4j_container)
