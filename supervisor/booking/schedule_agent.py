from langgraph.graph import StateGraph , START , END
from state import State

def schedule_agent(state:State) -> State:
    print('schedule agent hit')
    """
    # asks's user to provide schedule
    # if schedule is found - reservation
    # if schedule not found - try another schedule , exit , manual
    # if reservation Success - go to contact agent
    # if reservation Failure - try another schedule , exit , manual , standby
    # if asked for schedule - provide airline and the flights for selected airline
    # if user chooses the flight from provided flights -> reservation
    # user can exit at any point
    """

def schedule_node():
    print('schedule node hit')
    pass

def reservation_node():
    print('reservation node hit')
    pass

schedule_graph_builder = StateGraph(State)
schedule_graph_builder.add_node("schedule_agent", schedule_agent)
schedule_graph_builder.add_node("schedule", schedule_node)
schedule_graph_builder.add_node("reservation", reservation_node)
schedule_graph_builder.add_edge(START, "schedule_agent")

schedule_graph = schedule_graph_builder.compile()