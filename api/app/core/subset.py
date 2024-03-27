from typing import Optional

from app.constants import DEFAULT_QUERY_LIMIT
from app.enums.search_mode import VerificationTypeSearchMode


class Subset:

    def __init__(self, project, data_uuids=[]):
        self.data_uuids = data_uuids
        self.project = project

    def get_uuids(self):
        return self.data_uuids

    def get_view_record(
        self,
        record_id: bool = False,
        record_content: bool = True,
        record_meta_names: Optional[list] = None,
    ):
        """
        Get view related to the data record.
        Parameters
        ----------
        record_id: bool
            If true, return the record_id (specified at data import) in the 'record_id' field
        record_content: bool
            If true, record content will be included in the 'data' field
        record_meta_name: List
            List of record-level meta_names to include. If None, return all existing ones.
        Return
        ----------
        Dictionary always has a 'uuid' field and a 'record_metadata' field,
        and optional 'record_id', 'data' fields.

        """
        args = {
            "record_meta_names": record_meta_names,
            "data_u_list": self.data_uuids,
        }
        return_clauses = ["n.uuid as uuid"]
        q = [
            """
                MATCH (n: Record)
                WHERE n.uuid in $data_u_list
                OPTIONAL MATCH (r_meta:Metadata)-[:RECORD_META_OF]-(n) 
            """
        ]
        if record_id:
            return_clauses.append("n.record_id as record_id")
        if record_content:
            return_clauses.append("n.content as record_content")
        if record_meta_names is not None:
            args.update({"record_meta_names": record_meta_names})
            q.append("WHERE r_meta.name in $record_meta_names")

        return_clauses.append("record_metadata as record_metadata")

        q.append("WITH COLLECT(r_meta{.name, .value}) as record_metadata, n")
        q.append(f"RETURN {','.join(return_clauses)}")
        q.append("ORDER by n.record_id")

        result = self.project.database.read_db("\n".join(q), args=args)
        result = [dict(item) for item in result]
        return result

    def get_view_annotation(
        self,
        annotator_list: Optional[list] = None,
        label_names: Optional[list] = None,
        label_meta_names: Optional[list] = None,
    ):
        """
        Get annotation view.
        Parameters
        ----------
        annotator_list: list
            List of annotators names. If None, return for all annotators.
        label_names: list
            List of label names. If None, return for all Labels.
        label_meta_names:list
            List of label metadata names. If None, return for all possible label metadata.
            Returned label metadata Will be restricted to only the selected label names.
            E.g., If L1->m1, m2, L2->m2, a view with label_names=['l2'] and
            label_meta_names=['m1'] will return only l2 with a empty label_metadata_list1

        Return
        ----------
        {
            "uuid":uuid,
            "annotation_list": [] or list of labels}

        """
        args = {
            "annotator_list": annotator_list,
            "label_names": label_names,
            "label_meta_names": label_meta_names,
            "data_u_list": self.data_uuids,
        }
        q = [
            """
                MATCH (n: Record)
                WHERE n.uuid in $data_u_list
                OPTIONAL MATCH (n)--(an:Annotation)
            """
        ]

        if annotator_list is not None:
            q.append(f"WHERE an.annotator in $annotator_list")

        label_filter1 = (
            "" if label_names is None else "WHERE l1.label_name in $label_names"
        )
        label_filter2 = (
            "" if label_names is None else "WHERE l2.label_name in $label_names"
        )
        label_meta_filter1 = (
            ""
            if label_meta_names is None
            else "WHERE l_meta1.name in $label_meta_names"
        )
        label_meta_filter2 = (
            ""
            if label_meta_names is None
            else "WHERE l_meta2.name in $label_meta_names"
        )

        q.append(
            f"""
            // l1 for record_level labels
            OPTIONAL MATCH (l1:Label {{label_level:'record'}})-[:LABEL_OF]-(an) 
            {label_filter1}
            OPTIONAL MATCH (l_meta1:Metadata)-[:LABEL_META_OF]-(l1) 
            {label_meta_filter1}
            WITH COLLECT(l_meta1{{.name, .value}}) as label_metadata_list1, n, an, l1
            WITH COLLECT(l1{{.label_name, .label_value, .label_level, label_metadata_list:label_metadata_list1}}) as an_l1, n, an
            // l2 for span_level labels
            OPTIONAL MATCH (l2:Label {{label_level:'span'}})-[:LABEL_OF]-(an)
            {label_filter2}
            OPTIONAL MATCH (l_meta2:Metadata)-[:LABEL_META_OF]-(l2) 
            {label_meta_filter2}
            WITH COLLECT(l_meta2{{.name, .value}}) as label_metadata_list2 ,l2 ,n, an_l1, an
            WITH COLLECT(l2{{.label_name, .label_value, .label_level, .label_level, .start_idx, .end_idx, label_metadata_list:label_metadata_list2}}) as an_l2, n, an_l1, an
            WITH COLLECT(an{{.annotator,labels_record:an_l1, labels_span:an_l2}}) as annotation_list, n
            RETURN n.uuid as uuid, annotation_list as annotation_list
            ORDER by n.record_id
        """
        )
        result = self.project.database.read_db("\n".join(q), args=args)
        return [dict(item) for item in result]

    def get_view_verification(
        self,
        label_name: str,
        label_level: str,
        annotator: str,
        verifier_filter: Optional[list] = None,
        status_filter: Optional[str] = None,
    ):
        """
            Get the verification view for a subset, on a specific
            record-level label
            Future: span-level support

        Parameters
        ----------
        label_name : str
            Name of the label for verification.
        label_level : str["span"|"record"]
            level of the label for verification.
        annotator : str
            Annotator who provided the annotation to verify
            # FUTURE support list of annotators
        verifier_filter : list or None
            List of verifier who made the verification
        status_filter : str ["CONFIRMS","CORRECTS", "ALL"] | None
            Verification status filter, if the verification corrects or
            confirms the label in the original annotation.
        Returns
        ----------
        list [{"record_uuid":..., "verification_list": ...}],
        where verification_list is a list of verification objects
        in new to old order based on last updated time:
        {"annotator":...,
         "verifier":...,
         "verifification_status": [CORRECTS|CONFIRMS],
         "labels":...,
         "last_timestamp":...}


        """
        valid_status = [v.value for v in VerificationTypeSearchMode]
        if not (status_filter in valid_status or status_filter is None):
            raise Exception(f"Unsupported status filter {status_filter}.")
        if status_filter == "ALL":
            status_filter = None
        status_filter = (
            "|".join(valid_status) if status_filter is None else status_filter
        )

        if label_level == "span":
            raise NotImplementedError(
                "span-level verification retrieval not supported yet."
            )
        elif label_level == "record":
            q_verifier = (
                "WHERE ver.verifier in $verifier_filter"
                if verifier_filter is not None and len(verifier_filter) > 0
                else ""
            )

            q = f"""
                MATCH (n: Record)
                WHERE n.uuid in $uuid_list
                OPTIONAL MATCH (n)--(an:Annotation {{annotator:$annotator}})
                --(ver:Verification {{label_name:$label_name}})
                -[v_status:{status_filter}]-(l:Label) {q_verifier}
                WITH n.uuid as uuid, ver, an, v_status,
                    COLLECT({{label_value:l.label_value}}) as labels
                ORDER BY ver.last_timestamp DESC 
                WITH uuid, CASE an
                    WHEN null THEN []
                    ELSE 
                        COLLECT({{annotator:an.annotator,
                                verifier:ver.verifier,
                                labels:labels,
                                verification_status:TYPE(v_status),
                                last_timestamp:datetime(ver.last_timestamp).epochMillis}}) 
                    END as verification_list
                RETURN uuid as uuid, verification_list as verification_list
            """
            args = {
                "uuid_list": self.data_uuids,
                "label_name": label_name,
                "annotator": annotator,
                "verifier_filter": verifier_filter,
            }
            result = self.project.database.read_db(q, args)
            return [dict(item) for item in result]
        else:
            raise Exception(f"Unsupported label_level {label_level}")

    def suggest_similar(self, record_meta_name, limit=DEFAULT_QUERY_LIMIT):
        """
        Suggest similar data records. The most similar data points are defined as
        ones with the shortest distance according to the record_meta_name.
        Parameters
        ----------
        record_meta_name: name of the metadata used as distance measurement.
        limit: number of most similar record returned for each record in the subset.
        """
        q = """
            match (n:Record)-[:RECORD_META_OF {name:$record_meta_name}]-(m:Metadata) 
            where n.uuid in $uuid_list
            call {
            with n, m
            match (m2:Metadata) -[:RECORD_META_OF {name:$record_meta_name}]-(n2:Record)
            where n2.uuid <>n.uuid
            return  n2.uuid as uuid, n2.content as content
            order by gds.alpha.similarity.cosine(m2.value,m.value) DESC limit $limit 
            }
            return uuid
        """
        result = self.project.database.read_db(
            q,
            args={
                "uuid_list": self.data_uuids,
                "record_meta_name": record_meta_name,
                "limit": limit,
            },
        )
        return [item[0] for item in result]
