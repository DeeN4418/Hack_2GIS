#!/usr/bin/env python
from route_planner_agent.crew import RoutePlannerAgent

TEXT = """
Начинаю в 9:00 от Главного вокзала. 
К 10:00 — Краеведческий музей. 
После музея — сувенирная лавка. 
Обед в кафе «У Антона» в час дня. 
В 15:00 — прогулка по Центральному парку. 
Затем подъем на смотровую площадку на Проспекте Мира, 1. 
Вечер культурный: театр в 19:00, ужин в 
ресторане с панорамным видом в полдесятого вечера
"""

def run():
    """
    Run the crew.
    """
    # Replace with inputs you want to test with, it will automatically
    # interpolate any tasks and agents information
    inputs = {
        'location': 'Moscow Center',
        'attractions_count': '5',
        "city":"Perm",
        "time_interval":"4 hours",
        "text":TEXT

    }
    RoutePlannerAgent().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
