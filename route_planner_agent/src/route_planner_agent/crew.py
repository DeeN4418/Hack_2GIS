from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv

from route_planner_agent.models import Itinerary

load_dotenv()

@CrewBase
class RoutePlannerAgent():
    """RoutePlannerAgent crew"""
    
    # def __init__(self):
    #     self.yandex_llm = YandexGPTLLM()

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def travel_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['travel_agent'], # type: ignore[index]
            # llm=self.yandex_llm,
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def plan_trip_task(self) -> Task:
        return Task(
            config=self.tasks_config['plan_trip'], # type: ignore[index]
            agent=self.travel_agent(),
            output_json=Itinerary
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RoutePlannerAgent crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
