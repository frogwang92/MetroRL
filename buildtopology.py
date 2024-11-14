from facility.platform import Platform
from topology.node import Node
from topology.edge import Edge
from tr.linesegment import LineSegment

def build_topology(platforms, line_segments, default_interval=1):
    nodes = {}
    edges = []

    # Convert platforms to nodes
    for platform in platforms:
        nodes[platform.id] = Node(platform.dwell)

    # Convert line segments to nodes and edges
    for segment in line_segments:
        start_node = nodes[segment.start_platform.id]
        end_node = nodes[segment.end_platform.id]
        travel_time = segment.travel_time

        # Split the line segment into multiple nodes based on travel time
        num_intervals = travel_time // default_interval
        previous_node = start_node

        for i in range(1, int(num_intervals)):
            intermediate_node = Node(default_interval)
            nodes[f"{segment.start_platform.id}-{segment.end_platform.id}-{i}"] = intermediate_node
            edges.append(Edge(previous_node, intermediate_node, default_interval))
            previous_node = intermediate_node

        edges.append(Edge(previous_node, end_node, travel_time % default_interval))

    return nodes, edges

if __name__ == "__main__":
    # Create platform objects
    d1 = Platform(1, "d1", 120)
    s11 = Platform(2, "s11")
    s12 = Platform(3, "s12")
    s13 = Platform(4, "s13")
    s14 = Platform(5, "s14")
    s15 = Platform(6, "s15")
    s16 = Platform(7, "s16")
    d2 = Platform(8, "d2", 120)
    s21 = Platform(9, "s21")
    s22 = Platform(10, "s22")
    s23 = Platform(11, "s23")
    s24 = Platform(12, "s24")
    s25 = Platform(13, "s25")
    s26 = Platform(14, "s26")

    # Create line segment objects
    line_segments = [
        LineSegment(d1, s11),
        LineSegment(s11, s12),
        LineSegment(s12, s13),
        LineSegment(s13, s14),
        LineSegment(s14, s15),
        LineSegment(s15, s16),
        LineSegment(s16, d2),
        LineSegment(s14, s21),
        LineSegment(s21, s22),
        LineSegment(s22, s23),
        LineSegment(s23, s24),
        LineSegment(s24, s25),
        LineSegment(s25, s26),
        LineSegment(s26, s15)
    ]

    platforms = [d1, s11, s12, s13, s14, s15, s16, d2, s21, s22, s23, s24, s25, s26]

    nodes, edges = build_topology(platforms, line_segments)

    # Print the created nodes and edges
    for node_id, node in nodes.items():
        print(f"Node ID: {node_id}, Node: {node}")

    for edge in edges:
        print(edge)