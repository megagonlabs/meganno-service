from typing import Optional

import pydash
from app.constants import (
    DATABASE_503_RESPONSE,
    DEFAULT_QUERY_LIMIT,
    VALID_SCHEMA_LEVELS,
)
from app.core.assignment import Assignment
from app.core.database import Database
from app.core.schema import Schema
from app.core.statistic import Statistic
from app.core.utils import ValueNotExistsError
from app.enums.import_type import ImportType
from app.enums.search_mode import VerificationSearchMode, VerificationTypeSearchMode


class Project:

    def __init__(self, database: Database, project_name, description=""):
        self.database = database
        self.project_name = project_name
        name, found = create_or_get_project(
            database=database, project_name=project_name, description=description
        )
        if found == "EXISTS":
            print(
                f"Project '{name}' already exists in the database and has been retrieved."
            )
            self.project_name = name
        elif found == "CREATED":
            print(f"Project '{name}' was created.")
        elif found == "ERROR":
            print("Multiple project names are in the same database.")

    def import_data(
        self, file_type: str, url="", df_dict=None, column_mapping={}, dataset=""
    ):
        if ImportType.has(file_type.upper()) is False:
            raise NotImplementedError(
                f"Supported formats are: {', '.join([type.value for type in ImportType])}."
            )
        q_main = """
                MERGE (r:Record {record_id:toInteger(doc[$column_mapping_id]), dataset:$dataset})
                ON CREATE
                    SET r.content=doc[$column_mapping_content],
                        r.uuid=randomUUID(),
                        r.dataset=$dataset
                ON MATCH 
                    SET r.content=doc[$column_mapping_content] //update the content
                """
        args = {
            "column_mapping_id": column_mapping["id"],
            "column_mapping_content": column_mapping["content"],
        }
        if "metadata" in column_mapping.keys():
            record_meta_name = column_mapping["metadata"]
            q_meta = """         
                    MERGE (m:Metadata)- [:RECORD_META_OF {name:$record_meta_name}] -(r)
                    ON CREATE 
                    SET m.value = doc[$record_meta_name], m.uuid=randomUUID(), m.name=$record_meta_name
                    ON MATCH 
                    SET m.value = doc[$record_meta_name], m.name=$record_meta_name
                    """
            q_main += q_meta
            args.update({"record_meta_name": record_meta_name})
        q_main += "RETURN count(r)"

        if file_type.upper() == "CSV":
            """
            Importing data from a url to a csv format data. requried columns are id and content.
            also need to provide mapping from theses field to the column names in the csv file.
            """
            if url is None or len(url) == 0:
                raise Exception("'url' can not be None or empty.")
            if "id" not in column_mapping or "content" not in column_mapping:
                raise Exception("'column_mapping' is missing either 'id' or 'content'.")
            q_head = "LOAD CSV with HEADERS FROM $url as doc "
            q = q_head + q_main
            args.update({"url": url, "dataset": dataset})
            return self.database.write_db(q, args=args)[0][0]
        elif file_type.upper() == "DF":
            # error detection
            q_head = "UNWIND $df as doc"
            q = q_head + q_main
            args.update({"df": df_dict, "dataset": dataset})
            return self.database.write_db(q, args=args)[0][0]

    def export_data(self):
        q = """
            MATCH (r:Record)-[]-(n:Annotation)-[]-(l:Label) 
            RETURN r.record_id, r.content, n.annotator, l.label_name, l.label_value
            LIMIT 1000
        """
        args = {}
        return self.database.read_db(q, args=args)

    def __evaluator(self, node, var_name, val_name, config):
        ret = []
        arg = {}
        operator = config["operator"].upper()
        if operator not in ["==", "<", ">", "<=", ">=", "EXISTS", "CONFLICTS"]:
            raise Exception(f"Operator {operator} not supported")

        name = config["name"]
        for check in [name, node, var_name, val_name]:
            if not check.isidentifier():
                raise Exception(f"Invalid variable name {name})")

        ret.append(f"{node}.{var_name} = ${node}_name")
        arg.update({f"{node}_name": name})

        if operator == "==":
            value = config["value"]
            ret.append(f"{node}.{val_name} = ${node}_condition_value")
            arg.update({f"{node}_condition_value": value})

        if operator in ["<", ">", "<=", ">="]:
            value = float(config["value"])
            ret.append(f"toFloat({node}.{val_name}) {operator} ${node}_condition_value")
            arg.update({f"{node}_condition_value": value})
        return ret, arg

    def search(
        self,
        limit: int = DEFAULT_QUERY_LIMIT,
        skip: int = 0,
        # Data/record conditions, evluate in conjunction
        uuid_list: Optional[list] = None,
        keyword: Optional[str] = None,
        regex: Optional[str] = None,
        record_metadata_condition: Optional[dict] = None,
        # annotation conditions, evluate in conjunction
        annotator_list: Optional[list] = None,
        label_condition: Optional[dict] = None,
        label_metadata_condition: Optional[dict] = None,
        verification_condition: Optional[dict] = None,
    ):
        """
        Search for subset of records, based on conditions over the data records
        and its associated annotations (annotator, labels, and verification).
        The data conditions and annotation conditions evaluates in conjunction, separately.
        The function returns all the data records meeting all the data (e.g.keyword & regex) conditions
        and having *least one annotation* meeting all the annotation conditions.
        one annotation
        Parameters
        ----------
        limit: int
            Max number of rows returned
        skip: int
            If set, the result will start from the (skip+1)th row
        uuid_list:list
            If set, the search is limited to the records specified in the list
        keyword: str
            Keyword to match record content
        regex: str
            Regex to match record content
        record_metadata_condition: dict
            {"name": # name of the record-level metadata to filter on
            "operator": "=="|"<"|">"|"<="|">="|"exists",
            "value": # value to complete the expression}
        annotator_list: list
            List of annotator for the annotation.
        label_condition: dict
            Label condition of the annotation.
            {"name": # name of the label to filter on
            "operator": "=="|"exists"|"conflicts",
            "value": # value to complete the expression}
        label_metadata_condition: dict
            Label metadata condition of the annotation.
            Note this can be on different labels than label_condition
            {"label_name": # name of the associated label
            "name": # name of the label-level metadata to filter on
            "operator": "=="|"<"|">"|"<="|">="|"exists",
            "value": # value to complete the expression}
        verification_condition: dict
            verification condition of the annotation.
            {"label_name": # name of the associated label
             "search_mode":"ALL"|"UNVERIFIED"|"VERIFIED"}
        RETURN
        ---------
        Object: {'record_uuid': # meganno record reference,
                 "record_id": # record_id at import}
        """

        args = {
            "uuid_list": uuid_list,
            "keyword": keyword,
            "regex": regex,
            "annotator_list": annotator_list,
            "limit": int(limit),
            "skip": int(skip),
        }

        q_list = [
            "MATCH (n:Record)",
        ]
        # Record filters
        record_clauses = []
        if uuid_list is not None:
            record_clauses.append("n.uuid in $uuid_list")
        if keyword is not None:
            record_clauses.append("n.content contains $keyword")
        if regex is not None:
            record_clauses.append("n.content =~ $regex")
        if record_metadata_condition is not None:
            q_list[0] = "MATCH (n:Record)--(m_r:Metadata)"
            clause, arg = self.__evaluator(
                "m_r", "name", "value", record_metadata_condition
            )
            record_clauses.extend(clause)
            args.update(arg)
        if len(record_clauses) > 0:
            q_list.append(f"WHERE {' AND '.join(record_clauses)}")

        q_match = "MATCH (n)--(an:Annotation)"
        annotation_clauses = []
        # Annotation filters
        if annotator_list is not None:
            annotation_clauses.append("an.annotator in $annotator_list")

        # label filters
        conflict_filter = None
        if label_condition is not None:
            q_match += "--(l:Label)"
            if label_condition["operator"].upper() == "CONFLICTS":
                conflict_filter = """WITH n, apoc.convert.toSet(collect(apoc.convert.toJson(l.label_value))) 
                                    as candidates
                                    WHERE size(candidates)>1"""

            label_clauses, arg = self.__evaluator(
                "l", "label_name", "label_value", label_condition
            )
            annotation_clauses.extend(label_clauses)
            args.update(arg)

        # verification filters
        # start new search with a certain label_name
        if verification_condition is not None:
            label_name_to_verify = verification_condition["label_name"]
            verification_filter = verification_condition["search_mode"]
            args.update({"label_name_to_verify": label_name_to_verify})

            if (
                verification_filter == VerificationSearchMode.ALL.value
                or verification_filter is None
            ):
                pass
            elif verification_filter == VerificationSearchMode.VERIFIED.value:
                q_filter = "EXISTS((:Verification {label_name:$label_name_to_verify})-[:VERIFIES]-(an))"
                annotation_clauses.append(q_filter)
            elif verification_filter == VerificationSearchMode.UNVERIFIED.value:
                q_filter = "NOT EXISTS((:Verification {label_name:$label_name_to_verify})-[:VERIFIES]-(an))"
                annotation_clauses.append(q_filter)
            else:
                raise Exception(
                    f"Unsupported verification search mode {verification_filter}."
                )

        # label metadata filter
        label_meta_clauses = []
        q_match_label_meta = ""
        if label_metadata_condition is not None:
            label_name_restrict = label_metadata_condition["label_name"]
            q_match_label_meta = f"MATCH (m_l:Metadata)--(l_res:Label {{label_name:$label_name_restrict}})--(an)"
            label_meta_cluase, arg = self.__evaluator(
                "m_l", "name", "value", label_metadata_condition
            )

            label_meta_clauses.extend(label_meta_cluase)
            args.update({"label_name_restrict": label_name_restrict})
            args.update(arg)

        # populate cypher query
        if len(annotation_clauses) > 0 or len(label_meta_clauses) > 0:
            q_list.append(q_match)  # -> an:annotation object
        if len(annotation_clauses) > 0:
            q_list.append(f"WHERE {' AND '.join(annotation_clauses)}")
        if conflict_filter is not None:
            q_list.append(conflict_filter)
        if len(label_meta_clauses) > 0:
            q_list.append(q_match_label_meta)
            q_list.append(f"WHERE {' AND '.join(label_meta_clauses)}")

        q_list.append("RETURN DISTINCT n.uuid as record_uuid")
        q_list.append("SKIP $skip LIMIT $limit")

        result = self.database.read_db(query="\n".join(q_list), args=args)
        return [item["record_uuid"] for item in result]

    def get_data_by_uuid(self, uuid):
        q = """
            MATCH (n:Record)
            WHERE n.uuid = $uuid
            RETURN n
        """
        args = {"uuid": uuid}
        return self.database.read_db(q, args=args)

    def update_annotation_with_labels(
        self, label_list, annotator, record_uuid, overwrite=False
    ):
        """
        Create or update single Annotations, with already created list of labels.
        Rules as below:
        Each annotator can have at most one annotation for each data record.
        Update annotation to include only labels in label_list
        :params label_list: the uuids of labels to update the annotation
        :params annotator: annotator
        :params record_uuid: unique id for the data record
        :params overwrite: if set to true, existing labels of the annotation will be removed
                                 if is not included in the incoming label_list. Overwrite annotation.
        """
        q = """
            MATCH (r:Record {uuid:$record_uuid})
            MERGE (an:Annotation {record_uuid: $record_uuid, annotator: $annotator})-[:ANNOTATES] -> (r)
            ON CREATE 
                SET an.uuid = randomUUID(),
                    an.created_on=DateTime(),
                    an.annotator=$annotator,
                    an.record_uuid=$record_uuid
            WITH an
            // get existing lables
            OPTIONAL MATCH (l:Label)-[:LABEL_OF]-(an) 
            with collect (l.uuid) as old_labels, an 
            // remove old labels that does not exisits in new labels 
            OPTIONAL MATCH (l: Label) 
            WHERE l.uuid IN old_labels AND NOT l.uuid IN $new_labels
            CALL apoc.do.when($overwrite,
                               'DETACH DELETE l return count(l)',
                               '',
                               {l:l}) yield value as remove_count
            WITH old_labels, an
            // attach new labels to annotation node
            OPTIONAL MATCH (l: Label) 
            WHERE l.uuid IN $new_labels AND NOT l.uuid IN old_labels
            CALL apoc.do.when(l IS NULL,
                              '',
                              'MERGE (l)-[r:LABEL_OF]->(an) return r',
                              {l:l, an:an}) yield value as rel
            RETURN DISTINCT an.uuid as an_uuid"""

        return self.database.write_db(
            q,
            args={
                "new_labels": label_list,
                "annotator": annotator,
                "record_uuid": record_uuid,
                "overwrite": overwrite,
            },
        )

    def update_label(
        self,
        annotator,
        record_uuid,
        label_level,
        label_name,
        label_value,
        start_idx=None,
        end_idx=None,
        metadata_list=[],
    ):
        """
        Create or update labels. Rules as below:
        For span labels:
            For each annotation/annotator, there can be more than one span_level label of a certain name
            only check for duplicate spans, overlapping ones will be allowed
        For record labels:
            For each annotation/annotator, there's at most one record_level label of a certain name
        """
        q = []
        args = {
            "label_name": label_name,
            "label_value": label_value,
            "label_level": label_level,
            "annotator": annotator,
            "record_uuid": record_uuid,
        }
        main_q = """MERGE (l:Label {record_uuid: $record_uuid,
                                        annotator: $annotator, 
                                        label_level: $label_level, 
                                        label_name: $label_name"""

        if (
            label_level == "span"
            and pydash.is_integer(start_idx)
            and pydash.is_integer(end_idx)
        ):
            main_q += ", start_idx: $start_idx, end_idx: $end_idx})"
            args["start_idx"] = start_idx
            args["end_idx"] = end_idx
        else:
            main_q += "})"
        q.append(main_q)

        q.append(
            f"""
            ON MATCH
                SET l.label_value = $label_value // update labels
                
            ON CREATE
                SET l.uuid = randomUUID(),
                    l.label_value = $label_value
            RETURN l.uuid as label_uuid
            """
        )
        query = "\n".join(q)

        def query_function(tx, query, args):

            result = tx.run(query, args)
            label_uuid = result.single()["label_uuid"]

            # add label metadata
            if len(metadata_list) > 0:
                args_inner = {"label_uuid": label_uuid, "metadata_list": metadata_list}

                # check for duplicate metadata_name
                q_check = f"""
                    MATCH (n:Label {{uuid:$label_uuid}}) 
                    UNWIND $metadata_list as metadata
                    MATCH (n)-[r:LABEL_META_OF {{name:metadata.metadata_name}}]-(m:Metadata)
                    return count(m) as m_cnt, collect(r.name) as m_list
                    """

                result = tx.run(q_check, args_inner).single()
                if result["m_cnt"] > 0:
                    raise ValueError(
                        f"Metadata {result['m_list']} already existed for label {label_uuid}.\
                            No new metadata set for label. "
                    )

                # add metadata
                q = f"""
                MATCH (n:Label {{uuid:$label_uuid}}) 
                UNWIND $metadata_list as metadata
                CREATE (n)<-[:LABEL_META_OF {{name:metadata.metadata_name}}]-
                            (m:Metadata {{name:metadata.metadata_name,
                                value:metadata.metadata_value,
                            uuid:randomUUID()}})            
                return m.uuid as metadata_uuid
                """

                result = tx.run(q, args_inner)

            return label_uuid

        result = self.database.write_db_transction(
            query_func=query_function, query=query, args=args
        )
        return result

    def add_metadata_to_label(self, label_uuid, metadata_list):
        """
        Add metadata to existing label nodes.
        If any metadata_name in the metadata_list exists for label,
        the entire add metadata action will be discarded.

        :param label_uuid: the uuid of the label
        :param metadata_list: list of of metadata objects [{'metadata_name':xxx, 'metadata_value':xxx}]
        """
        args = {"label_uuid": label_uuid, "metadata_list": metadata_list}

        # check for duplicate metadata_name
        q_check = f"""
            MATCH (n:Label {{uuid:$label_uuid}}) 
            UNWIND $metadata_list as metadata
            MATCH (n)-[r:LABEL_META_OF {{name:metadata.metadata_name}}]-(m:Metadata)
            return count(m) as m_cnt, collect(r.name) as m_list
            """

        result = self.database.read_db(query=q_check, args=args)[0]
        if result["m_cnt"] > 0:
            raise ValueError(
                f"Metadata {result['m_list']} already existed for label {label_uuid}.\
                      No new metadata set for label. "
            )

        # add metadata
        q = f"""
        MATCH (n:Label {{uuid:$label_uuid}}) 
        UNWIND $metadata_list as metadata
        CREATE (n)<-[:LABEL_META_OF {{name:metadata.metadata_name}}]-
                    (m:Metadata {{name:metadata.metadata_name,
                        value:metadata.metadata_value,
                      uuid:randomUUID()}})            
        return m.uuid as metadata_uuid
        """

        result = self.database.write_db(query=q, args=args)
        return result

    def remove_label(
        self,
        annotator,
        record_uuid,
        label_name,
        label_level,
        start_idx=None,
        end_idx=None,
    ):
        args = {
            "label_name": label_name,
            "record_uuid": record_uuid,
            "annotator": annotator,
            "label_level": label_level,
        }
        q = []
        q.append(
            """
            MATCH (class:Label {record_uuid: $record_uuid,
                                annotator: $annotator,
                                label_level: $label_level,
                                label_name: $label_name
        """
        )
        if label_level == "span":
            q.append(", start_idx: $start_idx, end_idx: $end_idx")
            args["start_idx"] = start_idx
            args["end_idx"] = end_idx
        q.append("})")
        q.append(
            """
            DETACH DELETE class
            RETURN toInteger(count(class))
        """
        )
        return self.database.write_db(query="\n".join(q), args=args)[0][0]

    def annotate(self, record_uuid, labels, annotator):

        exist_uuid = self.get_data_by_uuid(uuid=record_uuid)
        if len(exist_uuid) == 0:
            raise ValueNotExistsError(record_uuid)

        # empty dictionary "{}" has length of 0
        if len(labels) == 0:
            reset_result = self.update_annotation_with_labels(
                label_list=[],
                annotator=annotator,
                record_uuid=record_uuid,
                overwrite=True,
            )
            if len(reset_result) == 0:
                return DATABASE_503_RESPONSE
            if len(reset_result) == 1:
                annotation_uuid = reset_result[0]["an_uuid"]
                return annotation_uuid

        new_labels = []
        if "span" in VALID_SCHEMA_LEVELS and "labels_span" in labels:
            for label in labels["labels_span"]:
                new_labels.append(
                    self.update_label(
                        label_name=label["label_name"],
                        start_idx=label["start_idx"],
                        end_idx=label["end_idx"],
                        label_value=label["label_value"],
                        label_level="span",
                        record_uuid=record_uuid,
                        annotator=annotator,
                        metadata_list=label.get("metadata_list", []),
                    )
                )
        if "record" in VALID_SCHEMA_LEVELS and "labels_record" in labels:
            for label in labels["labels_record"]:
                new_labels.append(
                    self.update_label(
                        label_name=label["label_name"],
                        label_value=label["label_value"],
                        label_level="record",
                        record_uuid=record_uuid,
                        annotator=annotator,
                        metadata_list=label.get("metadata_list", []),
                    )
                )
        update_result = self.update_annotation_with_labels(
            label_list=new_labels,
            annotator=annotator,
            record_uuid=record_uuid,
            overwrite=True,
        )
        if len(update_result) == 0:
            return DATABASE_503_RESPONSE
        if len(update_result) == 1:
            annotation_uuid = update_result[0]["an_uuid"]

        return annotation_uuid

    def annotate_batch(self, annotation_list, annotator):
        """ "
        Annotate for a batch of data record.
        Parameters
        -----------
        annotation_list: list of objects
            required fileds record_uuid, labels
        annotator: str
        Return
        ---------
        ret: list of object
            uuid: record_uuid
                annotation_uuid: if set succeed
                error: if set failed
        """
        ret = []
        for item in annotation_list:
            try:
                record_uuid = item["record_uuid"]
                labels = item["labels"]
                response = {"uuid": record_uuid}
                annotation_uuid = self.annotate(
                    record_uuid=record_uuid, labels=labels, annotator=annotator
                )
                response.update({"annotation_uuid": annotation_uuid})

            except ValueNotExistsError as ex:
                response.update(
                    {
                        "error": f"ValueNotExistsError: {record_uuid} does not exist in the database."
                    }
                )
            except KeyError as ex:
                response.update({"error": f"Bad request: {ex} is missing."})
            except Exception as ex:
                response.update({"error": f"Internal DB error {ex}"})
            ret.append(response)
        return ret

    def label(self, record_uuid, labels, annotator):
        exist_uuid = self.get_data_by_uuid(uuid=record_uuid)
        if len(exist_uuid) == 0:
            raise ValueNotExistsError(record_uuid)

        response_payload = {"uuid": record_uuid}
        label = labels[0]

        # empty dictionary "{}" has length of 0
        label_level = label["label_level"]
        label_value = label["label_value"]
        label_name = label["label_name"]
        if label_value is None:
            # remove
            if label_level.startswith("span"):
                self.remove_label(
                    annotator=annotator,
                    record_uuid=record_uuid,
                    label_level=label_level,
                    label_name=label_name,
                    start_idx=label["start_idx"],
                    end_idx=label["end_idx"],
                )
                return response_payload
            elif label_level.startswith("record"):
                self.remove_label(
                    annotator=annotator,
                    record_uuid=record_uuid,
                    label_level=label_level,
                    label_name=label_name,
                )
                return response_payload
        else:
            # add or update
            if label_level.startswith("span"):
                updated_label = self.update_label(
                    annotator=annotator,
                    record_uuid=record_uuid,
                    label_level=label_level,
                    label_name=label_name,
                    label_value=label_value,
                    start_idx=label["start_idx"],
                    end_idx=label["end_idx"],
                    metadata_list=label.get("metadata_list", []),
                )
                return response_payload
            elif label_level.startswith("record"):
                updated_label = self.update_label(
                    annotator=annotator,
                    record_uuid=record_uuid,
                    label_level=label_level,
                    label_name=label_name,
                    label_value=label_value,
                    metadata_list=label.get("metadata_list", []),
                )
                self.update_annotation_with_labels(
                    label_list=[updated_label],
                    annotator=annotator,
                    record_uuid=record_uuid,
                    overwrite=False,
                )
                return response_payload

    def verify(
        self,
        record_uuid,
        annotator_id,
        verified_by,
        label_name,
        label_level,
        labels,
    ):
        """Persist verification for an annotation.
        # Future add span-level support.
        Verification udpates rules:
        Record-level: create a new verification node if the label changes.
            Other wise, resuse verification and label nodes, update last_timestamp

        Parameters
        ----------
        record_uuid : str
            Unique identifier of data record of the annotation to be verified.
        annotator_id : str
            Unique identifier of the annotator of the annotation to be verified.
            An alternative interface will replace the (record_uuid, annotator_id)
            pair with annotation_uuid
        verified_by : str
            user_id of verifier
        label_name : str
            Name for label verified. Verification happens one label at a time.
        label_level : str
            record | span
        labels : list of label objects
            Record- or span-level label objects in the format of:
            {
                "label_name": "sentiment",
                "label_level": "record",
                "label_value": ["neu"]
            }
            Span-level label object example:
            {
                "label_name": "sen_span",
                "label_level": "span",
                "label_value": ["neu"],
                "start_idx": 10,
                "end_idx": 20
            }
        """
        if label_level not in VALID_SCHEMA_LEVELS:
            raise Exception(
                f"Unsupported label_level, expect: {', '.join(VALID_SCHEMA_LEVELS)}"
            )
        exist_uuid = self.get_data_by_uuid(uuid=record_uuid)
        if len(exist_uuid) == 0:
            raise ValueNotExistsError(record_uuid)
        if label_level == "span":
            raise NotImplementedError("span-level verification is not implemented.")
        elif label_level == "record":
            if len(labels) != 1:
                raise Exception(
                    "Do not provide more than one label for Record-levels labels"
                )
            l = labels[0]
            q_corrects = f"""
                MERGE (an)<-[:VERIFIES]
                    -(ver:Verification {{verifier:$apoc_verified_by}})
                    -[:{VerificationTypeSearchMode.CORRECTS.value}]
                    -(newL:Label {{label_value:$apoc_label_value}}) 
                ON CREATE
                SET ver.uuid=randomUUID()
                SET ver.verifier=$apoc_verified_by,
                    ver.label_name=$apoc_label_name,
                    ver.last_timestamp=DateTime(),
                    newL.uuid=randomUUID(),
                    newL.label_name=$apoc_label_name,
                    newL.label_value=$apoc_label_value,
                    newL.label_level=$apoc_label_level,
                    newL.record_uuid=an.record_uuid,
                    newL.annotator=$apoc_verified_by
                RETURN ver.uuid as verification_uuid"""

            q_confirms = f"""
                MERGE (an)<-[:VERIFIES]
                    -(ver:Verification {{verifier:$apoc_verified_by}})
                    -[:{VerificationTypeSearchMode.CONFIRMS.value}]-(l)
                ON CREATE
                SET ver.uuid=randomUUID()
                SET ver.verifier = $apoc_verified_by,
                    ver.label_name =$apoc_label_name,
                    ver.last_timestamp=DateTime()
                RETURN ver.uuid as verification_uuid"""

            q = f"""
                MATCH (an:Annotation) 
                WHERE an.record_uuid=$record_uuid AND an.annotator=$annotator_id
                OPTIONAL MATCH (l:Label {{label_name:$label_name, 
                                        label_value:$label_value}})
                --(an)
                CALL apoc.do.case([
                            l is null, "{q_corrects}",
                            l is not null, "{q_confirms}"
                            ],
                            "",
                            {{an:an, 
                            l:l, 
                            apoc_label_level:$label_level, 
                            apoc_label_value:$label_value, 
                            apoc_verified_by:$verified_by, 
                            apoc_label_name:$label_name}})
                YIELD value
                RETURN value as val"""

            if l["label_name"] == label_name and l["label_level"] == label_level:
                args = {
                    "label_value": l["label_value"],
                    "verified_by": verified_by,
                    "record_uuid": record_uuid,
                    "annotator_id": annotator_id,
                    "label_level": label_level,
                    "label_name": label_name,
                }
                result = self.database.write_db(query=q, args=args)
                if len(result) != 1:
                    raise Exception("Database error: set verification failed")
                return result[0]["val"]

    def get_schemas(self):
        return Schema(project=self)

    def get_statistics(self):
        return Statistic(project=self)

    def get_assignment_obj(self):
        return Assignment(project=self)

    def get_data_content(self, uuid_list: list = []):
        """
        Get the content of data give a list of uuids
        :param list uuid_list: list of record uuids to query
        :return: list of uuid and content pair
        """
        if isinstance(uuid_list, list) is False:
            raise TypeError("'uuid_list' must be a list.")
        q = """
            MATCH (n:Record)
            WHERE n.uuid in $uuid_list
            RETURN {uuid:n.uuid, data:n.content}
            ORDER BY n.record_id
        """
        ret = self.database.read_db(q, args={"uuid_list": uuid_list})
        return [item[0] for item in ret]

    def batch_update_metadata(self, record_meta_name, metadata_list: list = []):
        """
        Record metadata for records.

        :param str record_meta_name: name of the metadata
        :param metadata: list of objects in format {'uuid':.., 'value':..}

        :return: count of metadata items recorded.
        """
        if isinstance(metadata_list, list) is False:
            raise TypeError("'metadata_list' must be a list.")

        for metadata in metadata_list:
            if "uuid" not in metadata.keys() or "value" not in metadata.keys():
                raise ValueError(
                    "Objects in 'metadata_list' must follow the format {'uuid':.., 'value':..}"
                )
        q = """
            UNWIND $data as p
            MATCH (r:Record {uuid:p.uuid})
            MERGE (m:Metadata)- [:RECORD_META_OF {name:$record_meta_name}] -(r)
            ON CREATE 
                SET m.value = p.value, m.uuid=randomUUID(), m.name=$record_meta_name
            ON MATCH 
                SET m.value = p.value, m.name=$record_meta_name
            RETURN count(m) as count"""
        args = {"data": metadata_list, "record_meta_name": record_meta_name}
        return self.database.write_db(q, args=args)[0][0]

    def database_check(self):
        try:
            self.database.verify_connectivity()
            return True
        except Exception:
            return False


def create_constraints(database):
    # dataset, id or uuid be the unique identifier,
    # constraint on multiple properties is a enterprise-only function
    # pass for now.
    pass


def create_index(database):
    database.write_db(
        """
        CREATE INDEX index_data_uuid IF NOT EXISTS
        FOR (n:Record)
        ON (n.uuid);
    """
    )
    database.write_db(
        """
        CREATE INDEX index_annotation_annotator IF NOT EXISTS 
        FOR (a:Annotation) 
        
        on (a.annotator)
    """
    )


def create_or_get_project(database, project_name, description=""):
    q = """
        MATCH (n:Project) with count(n) as cnt
        CALL apoc.do.case([
            cnt=0, "create (nn:Project) 
                    SET 
                        nn.name=$apoc_project_name,
                        nn.description=$apoc_description,
                        nn.created_on=DateTime(),
                        nn.uuid=randomUUID() 
                        return nn.name as name, 'CREATED' as found ",
            cnt=1, "match (nn:Project) return nn.name as name, 'EXISTS' as found",
            cnt>1, "return '', 'ERROR'"], '', {apoc_project_name: $project_name, apoc_description: $description}) yield value
        return value
    """
    result = database.write_db(
        q, args={"project_name": project_name, "description": description}
    )[0][0]
    project_name, found = result["name"], result["found"]
    if found == "CREATED":
        # create_index(database)
        # skipping index creation to avoid neo4j caching error
        # need to fix later for efficiency
        create_constraints(database)
    return project_name, found
