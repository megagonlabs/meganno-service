import json
import unittest

import pytest
from app.core.agent_manager import AgentManager
from conftest import TestCore, ValueStorage


@pytest.mark.order(4)
class TestAgentCore(TestCore):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ag = AgentManager(cls.project)

    def test_core_register_agent(self):
        model_config = {"model": "gpt-3.5", "temperature": 0}
        created_by = "test_user1"
        provider_api = "openai:chat_completion"
        prompt_template = "give me the answer for {{}}"
        result = self.ag.register_agent(
            created_by=created_by,
            model_config=model_config,
            prompt_template=prompt_template,
            provider_api=provider_api,
        )

        self.assertTrue(result["agent_uuid"].startswith("agent_"))

    def test_core_register_agent_invalid(self):
        pass

    @pytest.mark.order(after="test_core_register_agent")
    def test_core_list_agents(self):
        result = self.ag.list_agents()

        self.assertTrue(len(result) == 1)
        self.assertEqual(result[0]["provider_api"], "openai:chat_completion")

    @pytest.mark.order(after="test_core_list_agents")
    def test_core_persist_job(self):
        pass

    @pytest.mark.order(after="test_core_list_agents")
    def test_core_persist_job_invalid(self):
        pass

    @pytest.mark.order(after="test_core_persist_job")
    def test_core_list_jobs(self):
        pass


if __name__ == "__main__":
    unittest.main()
