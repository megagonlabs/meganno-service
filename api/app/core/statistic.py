import itertools
import json
from collections import Counter

import numpy as np
import pandas as pd
import pydash
from app.constants import (
    DEFAULT_STATISTIC_LABEL_DISTRIBUTION_AGGREGATION_FUNCTION,
    SUPPORTED_AGGREGATION_FUNCTIONS,
)
from sklearn.manifold import TSNE


def majority_vote(lst):
    c = Counter([",".join(item) for item in lst])
    common = c.most_common(2)
    # checking for ties
    if len(common) < 2:
        return common[0][0]
    else:
        c1, c2 = common
        return "tied_annotations" if c1[1] == c2[1] else c1[0]


def cohen_kappa(ann1, ann2):
    """Computes Cohen kappa for pair-wise annotators.
    :param ann1: annotations provided by first annotator
    :type ann1: list
    :param ann2: annotations provided by second annotator
    :type ann2: list
    :rtype: float
    :return: Cohen kappa statistic
    Implementation from https://towardsdatascience.com/inter-annotator-agreement-2f46c6d37bf3
    """
    count = 0
    for an1, an2 in zip(ann1, ann2):
        if an1 == an2:
            count += 1
    A = count / len(ann1)  # observed agreement A (Po)

    uniq = set(ann1 + ann2)
    E = 0  # expected agreement E (Pe)
    for item in uniq:
        cnt1 = ann1.count(item)
        cnt2 = ann2.count(item)
        count = (cnt1 / len(ann1)) * (cnt2 / len(ann2))
        E += count

    return round((A - E) / (1 - E), 4)


class Statistic:
    def __init__(self, project) -> None:
        self.project = project

    def get_record_count(self):
        q = """
            MATCH (corpus:Record) 
            RETURN COUNT(DISTINCT corpus) AS total
        """
        result = self.project.database.read_db(query=q)[0]

        return int(result["total"])

    def get_label_progress(self):
        """
        Get the overall label statistic
        :return json object
            annotated: count of data points that has at least one label
                        from any annotator for any label_name
            total: total number of data records
        """
        q = """
            MATCH (corpus:Record) 
            OPTIONAL MATCH (l:Label)-[]-(an:Annotation)-[rel:ANNOTATES]->(r:Record)
            RETURN COUNT(DISTINCT corpus) AS total,
                   COUNT(DISTINCT r) AS annotated
        """
        result = self.project.database.read_db(query=q)[0]
        return {key: result[key] for key in result._Record__keys}

    def get_label_distributions(
        self,
        label_name: str = "",
        annotator_list: list = [],
        aggregation: str = DEFAULT_STATISTIC_LABEL_DISTRIBUTION_AGGREGATION_FUNCTION,
        include_unlabeled: bool = False,
    ):
        if include_unlabeled is True:
            raise NotImplementedError("'include_unlabeled' is not supported.")
        if len(annotator_list) > 0:
            raise NotImplementedError("'annotator_list' is not supported.")
        q = """
            MATCH (l:Label)-[]-(an:Annotation)-[]-(r:Record) 
            WHERE l.label_name = $label_name 
            RETURN r.uuid as uuid, collect(l.label_value) as label_list
            """
        result = self.project.database.read_db(query=q, args={"label_name": label_name})
        # Aggregate over annotators

        if aggregation not in SUPPORTED_AGGREGATION_FUNCTIONS:
            raise NotImplementedError(
                f"Supported functions are: {', '.join(SUPPORTED_AGGREGATION_FUNCTIONS)}."
            )
        agg_labels = [majority_vote(item["label_list"]) for item in result]
        return dict(Counter(agg_labels))

    def get_annotator_contributions(
        self, label_name: str = "", annotator_list: list = []
    ):
        if len(annotator_list) > 0:
            raise NotImplementedError("'annotator_list' is not supported.")
        q = """
            Match (l:Label)-[]-(an:Annotation)
            RETURN an.annotator as annotator, count(l) as contribution
        """
        result = self.project.database.read_db(query=q)
        return dict(result)

    def get_annotator_agreements(self, label_name: str = "", annotator_list: list = []):
        if len(annotator_list) > 0:
            raise NotImplementedError("'annotator_list' is not supported.")
        q = """
            MATCH (l:Label)-[]-(an:Annotation)-[]-(r:Record) 
            WHERE l.label_name = $label_name 
            RETURN r.uuid as uuid, l.label_value as label_list, an.annotator as annotator
            """
        result = self.project.database.read_db(query=q, args={"label_name": label_name})

        if len(result) == 0:
            return {}

        df = pd.DataFrame(result, columns=["uuid", "label_list", "annotator"])
        # convert label to a single string.
        df["label_list"] = df.apply(lambda x: ",".join(x["label_list"]), axis=1)
        df = df.pivot(index="uuid", columns="annotator", values="label_list")
        # filling in empty cells
        df = df.fillna("NULL")
        annotator_list = df.columns.to_list()
        return {
            f"{an1},{an2}": cohen_kappa(df[an1].to_list(), df[an2].to_list())
            for an1, an2 in itertools.product(annotator_list, annotator_list)
        }

    def get_embedding_aggregated_label(
        self, label_name: str = "", embedding_type: str = None
    ):
        """
        Get aggregated label along with embedding projected to 2d space.
        Aggregate using majority vote.
        Configurable parameters:
            - label_name
            - embedding_type
        :returns list of object in format {'x_axis':.. , 'y_axis':.., 'agg_label':..}
        """
        if embedding_type is None or len(embedding_type) == 0:
            raise ValueError("'type' can not be None or empty.")
        embedding_name = embedding_type
        # Future: assert the existence of such embdding as metadata
        q = """
            MATCH (l:Label)-[*2]-(r:Record)-[:RECORD_META_OF {name:$embedding_name}]-(m:Metadata)
            WHERE l.label_name = $label_name 
            RETURN r.uuid as uuid, m.value as embedding, collect(l.label_value) as label_list
        """
        result = self.project.database.read_db(
            query=q, args={"label_name": label_name, "embedding_name": embedding_name}
        )
        if pydash.is_empty(result):
            raise ValueError(f'No "{embedding_name}" as metadata.')
        df = pd.DataFrame(result, columns=["uuid", "embedding", "label_list"])
        # Use majority vote to aggregate labels
        df["agg_label"] = df.apply(lambda x: majority_vote(x["label_list"]), axis=1)
        # calculate 2d projection
        tsne = TSNE(n_components=2, random_state=0, perplexity=30, n_iter=1000)
        projection_2d = tsne.fit_transform(np.array(df["embedding"].to_list()))
        df_2d = pd.DataFrame(projection_2d, columns=["x_axis", "y_axis"])
        if len(df) != len(df_2d):
            raise Exception("Projection and original embedding counts don't match.")
        final_df = pd.concat([df, df_2d], axis=1)[["x_axis", "y_axis", "agg_label"]]
        return json.loads(final_df.to_json(orient="records"))
