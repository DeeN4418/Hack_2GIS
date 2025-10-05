from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv

from route_planner_agent.models import Itinerary, ExtractedPlaces

load_dotenv()

@CrewBase
class RoutePlannerAgent():
    """RoutePlannerAgent crew"""
    
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def extracter(self) -> Agent:
        return Agent(
            config=self.agents_config['extracter'],
            verbose=True
        )
        
    @agent
    def time_sorter(self) -> Agent:
        return Agent(
            config=self.agents_config['time_sorter'],
            verbose=True
        )

    @task
    def extract_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_task'],
            agent=self.extracter(),
            output_json=ExtractedPlaces  # Новая модель для извлеченных мест
        )
    
    @task
    def time_sorting_task(self) -> Task:
        return Task(
            config=self.tasks_config['time_sorting_task'],
            agent=self.time_sorter(),
            context=[self.extract_task()],
            output_json=Itinerary  # Существующая модель для итогового маршрута
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RoutePlannerAgent crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )