class Assignment:
    """
    Handling workload(subset) assignment to annotators
    """

    def __init__(self, project):
        self.project = project

    def set_assignment(self, subset, annotator, assigned_by):
        """
        creating new assignment for 'annotator', with data points in susbet
        :param susbet: list of data uuids
        :param annotator: annotator user ID (not name)
        :param assigned_by: user ID of the assigner
        """
        if not isinstance(subset, list):
            raise Exception("'subset' should be a list.")
        q = """
            CREATE (s:Subset)
            SET s.uuid=randomUUID(),s.created_on=DateTime(),
                s.data_uuid_list = $data_uuid_list
            WITH s MATCH (p:Project {name:$project_name})
            WITH s,p MERGE (s) -[rel:ASSIGNED_TO 
                                    {annotator:$annotator, 
                                    assigned_by:$assigned_by}] - (p)
            RETURN s.uuid as uuid
        """

        args = {
            "project_name": self.project.project_name,
            "annotator": annotator,
            "data_uuid_list": subset,
            "assigned_by": assigned_by,
        }
        result = self.project.database.write_db(q, args=args)
        if len(result) == 1:
            return {
                "uuid": result[0]["uuid"],
            }
        else:
            return False

    def get_assignment(self, annotator, latest_only=False):
        """
        get assignement to annotator
        :param annotator: querying user ID
        :param latest_only: boolean, if ture, only return the latest assignment
        """
        if annotator is None or len(annotator) == 0:
            raise Exception("Annotator cannot be None or empty.")
        q = """
            MATCH (s:Subset)-[rel:ASSIGNED_TO {annotator:$annotator}]
                   -(p:Project {name:$project_name})
            RETURN s.data_uuid_list as data_uuid_list, 
                   s.created_on as created_on,
                   rel.assigned_by as assigned_by
            """

        if latest_only:
            q = q + "ORDER BY s.created_on DESC LIMIT 1"

        args = {
            "project_name": self.project.project_name,
            "annotator": annotator,
        }

        result = self.project.database.read_db(q, args=args)
        return result
