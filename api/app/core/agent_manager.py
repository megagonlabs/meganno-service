import json

import pydash
from app.core.project import Project


class AgentManager:

    def __init__(self, project: Project) -> None:
        """
        Class managing automated (LLM) agents
        """
        self.project = project

    def check_model_config(self, config):
        try:
            return pydash.is_json(json.dumps(config))
        except:
            return False

    def check_template(self, template):
        return pydash.is_string(template)

    def register_agent(self, created_by, model_config, prompt_template, provider_api):
        """Register automated agent with backend service

        Parameters
        ----------
        created_by : str
            user_id of user who created and registered the agent
        model_config : json
            Model configuration object, minimal fields:
            - provider
            - model_name
        prompt_template : str
            Serialized prompt template
        provider_api : str
            Name of specific api provider eg. 'openai:chat'

        Returns
        -----------
        object with unique agent id.
        """
        # check input validity
        if not self.check_model_config(model_config):
            raise Exception("Invalid model configuration.")
        if not self.check_model_config(prompt_template):
            raise Exception("Invalid prompt template.")
        if not self.check_model_config(provider_api):
            raise Exception("Invalid api provider.")

        q = """
            CREATE (ag:Agent) 
            SET ag.uuid="agent_"+randomUUID(), 
                ag.create_on=DateTime(),
                ag.created_by=$created_by,
                ag.model_config=$model_config,
                ag.prompt_template=$prompt_template,
                ag.provider_api=$provider_api
            WITH ag MATCH (p:Project {name:$project_name})
            WITH p,ag MERGE (ag) -[rel:AGENT_OF] -> (p)
            RETURN ag.uuid as uuid
        """
        args = {
            "project_name": self.project.project_name,
            "created_by": created_by,
            "model_config": json.dumps(model_config),
            "prompt_template": prompt_template,
            "provider_api": provider_api,
        }
        result = self.project.database.write_db(q, args=args)
        if len(result) == 1:
            return {
                "agent_uuid": result[0]["uuid"],
            }
        else:
            return False

    def list_agents(
        self,
        created_by_filter=None,
        provider_filter=None,
        api_filter=None,
        show_job_list=False,
    ):
        """List registered agents.
        Parameters
        ----------
        created_by_filter : list(str)
            List of user_id. if not None, filter to only return agents created by
            users in the list.
        provider_filter: str
            Return the only the agent with the specified provider
        api_filter:list(str)
            Return the only the agent with the specified api
        show_job_list: bool
            if True, also return the list uuids of jobs of the agent.

        Returns
        ---------
        list of agents and properties.
        """
        args = {
            "project_name": self.project.project_name,
        }
        q_filter_clauses = []
        if created_by_filter is not None:
            q_filter_clauses.append("ag.created_by in $created_by")
            args.update({"created_by": created_by_filter})
        if provider_filter is not None:
            q_filter_clauses.append("ag.provider_api STARTS with $provider_filter")
            args.update({"provider_filter": provider_filter + ":"})
        if api_filter is not None:
            q_filter_clauses.append("ag.provider_api ENDS with $api_filter")
            args.update({"api_filter": ":" + api_filter})

        if len(q_filter_clauses) > 0:
            condition = " AND ".join(q_filter_clauses)
            q_filter = f"WHERE {condition}"
        else:
            q_filter = ""

        q_filter_return_job = (
            """OPTIONAL MATCH (j:Job)-[:JOB_OF]-(ag)
            WITH ag, collect(j.uuid) as job_list
             """
            if show_job_list
            else ""
        )

        q_return_job = ", job_list" if show_job_list else ""

        q = f"""
            MATCH (ag: Agent)-[]-(p:Project {{name:$project_name}}) {q_filter}
            {q_filter_return_job}
            RETURN ag.uuid as uuid , ag.model_config as model_config,
             ag.prompt_template as prompt_template, ag.provider_api as provider_api, 
             ag.created_by as created_by {q_return_job}
            """

        result = self.project.database.read_db(q, args=args)
        return [dict(item) for item in result]

    def persist_job(
        self, job_uuid, issued_by, agent_uuid, label_name, annotation_uuid_list
    ):
        """Given annoations for a subset, persit as a job for the project.
        Parameters
        ----------
        job_uuid : str
            Unique id of job, also used as the annotator for corresponding annotations
        issued_by : str
            user_id of user who issued the job
        agent_uuid : str
            Uuid of the agent used to run the job.
        label_name : str
            Name of the label generated by the agent in the job. Current version
            supports a single label_name per job. A valid label_name needs to exits
            in the schema.
        annotation_uuid_list : list(str)
            List of annotation node uuid generated from the job.

        Returns
        ---------
        Job uuid.

        Future checks
        -------
        1. verify annotator == job_uuid
        2. verify agent_uuid is valid in db
        3. verify label_name in schema
        """

        # if job_uuid alreday exists, only adding new links to annotation nodes
        q = """
            MATCH (ag:Agent {uuid:$agent_uuid})
            MERGE (j:Job {uuid:$job_uuid})-[:JOB_OF]-(ag)
            ON CREATE
            SET j.uuid=$job_uuid,
                j.create_on=DateTime(),
                j.issued_by=$issued_by,
                j.agent_uuid=$agent_uuid,
                j.label_name=$label_name
            WITH j
            MATCH (an:Annotation) where an.uuid in $annotation_uuid_list
            MERGE (j)-[:CONTAINS]->(an) 
            RETURN DISTINCT j.uuid as uuid, count(an) as an_cnt
        """
        args = {
            "job_uuid": job_uuid,
            "issued_by": issued_by,
            "agent_uuid": agent_uuid,
            "label_name": label_name,
            "annotation_uuid_list": annotation_uuid_list,
        }
        result = self.project.database.write_db(q, args=args)
        if len(result) == 1:
            return {
                "job_uuid": result[0]["uuid"],
                "annotation_cnt": result[0]["an_cnt"],
            }
        else:
            return False

    def list_jobs(self, filter_by, filter_values, show_agent_details=False):
        """List jobs with potential querying filters
        Parameters
        ----------
        filter_by : str ["agent_uuid" | "issued_by" | "uuid"] | None
            optional filter field
        filter_values : list
            list of uuids of entity specified in 'filter_by'
        show_agent_details : boolean
            If true, also return agent config.
        """
        FILTER_TYPES = ["agent_uuid", "issued_by", "uuid"]
        if not (filter_by is None or filter_by in FILTER_TYPES):
            raise NotImplementedError(
                f'Supported filter_by types are: {", ".join(FILTER_TYPES)}'
            )

        q_filter = f"WHERE j.{filter_by} in $filter_values"

        if show_agent_details:
            q = f"""
                MATCH (j: Job)-[:JOB_OF]-(ag:Agent) {'' if filter_by is None else q_filter}
                RETURN j.uuid as job_uuid, j.issued_by as job_issued_by,
                    j.agent_uuid as agent_uuid, j.label_name as job_label_name,
                    ag.created_by as agent_created_by,
                    ag.model_config as agent_model_config,
                    ag.prompt_template as agent_prompt_template,
                    ag.provider_api as agent_provider_api

                """
        else:
            q = f"""
                MATCH (j: Job) {'' if filter_by is None else q_filter}
                RETURN j.uuid as job_uuid, j.issued_by as job_issued_by,
                    j.agent_uuid as agent_uuid, j.label_name as job_label_name 
                """
        args = {"filter_values": filter_values}

        result = self.project.database.read_db(q, args=args)
        return result
