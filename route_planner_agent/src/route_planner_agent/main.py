#!/usr/bin/env python
from route_planner_agent.crew import RoutePlannerAgent

def run():
    """
    Run the crew.
    """
    # Replace with inputs you want to test with, it will automatically
    # interpolate any tasks and agents information
    inputs = {
        'location': 'Moscow Center'
    }
    RoutePlannerAgent().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
