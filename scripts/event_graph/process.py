import math
import matplotlib.pyplot as plt
import networkx as nx
import json

def mean(values):
    return sum(values) / len(values)

def consolidate_whitespace(string):
    while '  ' in string:
        string = string.replace('  ', ' ')
    return string

with open("output.json") as json_file:
    event_rules = json.load(json_file)

G = nx.MultiDiGraph()
# Conditional scheduling nodes
for event_rule in event_rules:
    if "ConditionalScheduling" in event_rule["event_routine"].keys():
        for conditional_scheduling in event_rule["event_routine"][
            "ConditionalScheduling"
        ]:
            G.add_node(event_rule["event_expression"].replace("_", "\n").title())
            G.add_node(
                conditional_scheduling["follow_up_event"].replace("_", "\n").title()
            )
            G.add_edge(
                event_rule["event_expression"].replace("_", "\n").title(),
                conditional_scheduling["follow_up_event"].replace("_", "\n").title(),
                weight=4,
            )
            G.add_edge(
                conditional_scheduling["follow_up_event"].replace("_", "\n").title(),
                "events_int".replace("_", "\n").title(),
                weight=4,
            )
G.add_edge(
    "events_ext".replace("_", "\n").title(),
    "events_int".replace("_", "\n").title(),
    weight=4,
)

# pos = nx.spring_layout(G, iterations=10000, seed=107)
pos = nx.circular_layout(G)
nx.draw(
    G,
    pos,
    width=4,
    linewidths=4,
    node_size=2400,
    node_color="k",
    alpha=0.4,
    edge_color="k",
    arrowsize=20,
    with_labels=False,
)
# Add event names
for p in pos:  # lower text positions
    plt.text(pos[p][0], pos[p][1], p, family="serif", ha="center", va="center", wrap=True, size=8)
# Add conditional and state transition expressions
legend_index = 0
# Conditions
for event_rule in event_rules:
    if "ConditionalScheduling" in event_rule["event_routine"].keys():
        for conditional_scheduling in event_rule["event_routine"][
            "ConditionalScheduling"
        ]:
            first_node = event_rule["event_expression"].replace("_", "\n").title()
            second_node = conditional_scheduling["follow_up_event"].replace("_", "\n").title()
            first_pos = pos[first_node]
            second_pos = pos[second_node]
            middle_pos = [mean([first_pos[0], second_pos[0]]), mean([first_pos[1], second_pos[1]])]
            angle = math.degrees(math.atan2(first_pos[1]-second_pos[1],first_pos[0]-second_pos[0]))+90
            condition = conditional_scheduling["condition"].replace("\n", " ").replace("self . ", " ")
            plt.text(middle_pos[0], middle_pos[1], "~", color="#999999", family="serif", ha="center", va="center", rotation=angle, wrap=True, size=24)
            plt.text(middle_pos[0], middle_pos[1] - 0.05, "$i_{}$".format(legend_index), color="k", family="serif", ha="center", va="center", wrap=True, size=8)
            plt.text(0.95, -1.3-0.07*legend_index, "$i_{}$: {}".format(legend_index, condition), color="k", family="serif", ha="right", va="center", wrap=False, size=8)
            legend_index += 1
# State transitions
follow_up_index = 0
index_from_expression = {}
legend_index = 0
for event_rule in event_rules:
    if "ConditionalScheduling" in event_rule["event_routine"].keys():
        for conditional_scheduling in event_rule["event_routine"][
            "ConditionalScheduling"
        ]:
            second_node = conditional_scheduling["follow_up_event"].replace("_", "\n").title()
            second_pos = pos[second_node]
            plt.text(second_pos[0], second_pos[1]-0.22, "$\Delta_{}$".format(follow_up_index), color="k", family="serif", ha="center", va="center", wrap=True, size=8)
            index_from_expression[conditional_scheduling["follow_up_event"]] = follow_up_index
            follow_up_index += 1
for event_rule in event_rules:
    if "UnconditionalStateTransition" in event_rule["event_routine"].keys() and event_rule["event_expression"] in index_from_expression.keys():
        plt.text(1.2, 1.05-0.07*legend_index, "$\Delta_{}$".format(index_from_expression[event_rule["event_expression"]]), color="k", family="serif", ha="left", va="center", wrap=False, size=8)
        event_routine = event_rule["event_routine"]["UnconditionalStateTransition"] \
            .rstrip("Ok(())\n}") \
            .lstrip("{\n") \
            .replace("\n", " ") \
            .replace(";", ";\n") \
            .replace("{", "{\n") \
            .replace("}", "}\n") \
            .replace(",", ",\n")
        event_routine = consolidate_whitespace(event_routine).replace("self . ", " ").replace(" . clone()", "")
        line_count = event_routine.count("\n")
        for i in range(0, line_count):
            plt.text(1.25, 1.05-0.07*(legend_index+i), event_routine.split("\n")[i], color="k", family="serif", ha="left", va="center", wrap=False, size=8)
        legend_index += line_count

# Make the events_ext to events_int event-cancelling edge dotted
angle = math.atan2(pos["Events\nInt"][1] - pos["Events\nExt"][1], pos["Events\nInt"][0] - pos["Events\nExt"][0])
total_length = math.sqrt((pos["Events\nInt"][1] - pos["Events\nExt"][1])**2 + (pos["Events\nInt"][0] - pos["Events\nExt"][0])**2)
start_x = pos["Events\nExt"][0] + 0.16*math.cos(angle)
start_y = pos["Events\nExt"][1] + 0.16*math.sin(angle)
end_x = pos["Events\nExt"][0] + (total_length-0.22)*math.cos(angle)
end_y = pos["Events\nExt"][1] + (total_length-0.22)*math.sin(angle)
plt.plot([end_x, start_x], [end_y, start_y], color='w', linestyle=':', linewidth=5)

# Setup followup -> d_int delay markers
for node in pos.keys():
    if node not in ["Events\nInt", "Events\nExt"]:
        angle = math.atan2(pos["Events\nInt"][1] - pos[node][1], pos["Events\nInt"][0] - pos[node][0])
        total_length = math.sqrt((pos["Events\nInt"][1] - pos[node][1])**2 + (pos["Events\nInt"][0] - pos[node][0])**2)
        x = pos[node][0] + 0.16*math.cos(angle)
        y = pos[node][1] + 0.16*math.sin(angle)
        plt.text(x, y+0.05, "$\sigma$", color="k", family="serif", ha="left", va="center", wrap=False, size=8)

plt.savefig("event_graph.png", bbox_inches="tight")
