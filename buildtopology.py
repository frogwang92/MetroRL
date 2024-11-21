import networkx as nx
"""
This module builds a topology of nodes and edges from given platforms and line segments,
and calculates coordinates for the nodes using NetworkX.
Classes:
    Platform: Represents a platform with an ID and dwell time.
    Node: Represents a node in the topology.
    Edge: Represents an edge between two nodes in the topology.
    LineSegment: Represents a line segment between two platforms.
Functions:
    build_topology(platforms, line_segments, default_interval=1):
        Converts platforms to nodes and line segments to edges, splitting line segments
        into multiple nodes based on travel time.
    calc_coordinates_with_networkx(nodes, edges):
        Calculates the coordinates of nodes using NetworkX's spring layout algorithm.
Usage:
    Create Platform and LineSegment objects, then use build_topology to create nodes and edges.
    Use calc_coordinates_with_networkx to calculate the coordinates of the nodes.
"""

from facility.platform import Platform
from topology.node import Node
from topology.edge import Edge
from tr.linesegment import LineSegment

def build_topology(platforms, line_segments, default_interval=1):
    nodes = {}
    edges = []
    segments = {}
    node2segments = {}

    # Convert platforms to nodes
    for platform in platforms:
        nodes[platform.id] = Node(platform.id, platform.dwell)

    # Convert line segments to nodes and edges
    for segment in line_segments:
        start_node = nodes[segment.start_platform.id]
        end_node = nodes[segment.end_platform.id]
        travel_time = segment.weight
        segments[segment] = (start_node.id, end_node.id)
        node2segments[start_node.id] = segment
        
        # Split the line segment into multiple nodes based on travel time
        num_intervals = travel_time // default_interval
        previous_node = start_node

        for i in range(1, int(num_intervals)):
            intermediate_node_id = f"{segment.start_platform.id}-{segment.end_platform.id}-{i}"
            intermediate_node = Node(intermediate_node_id, default_interval)
            nodes[intermediate_node_id] = intermediate_node
            node2segments[intermediate_node_id] = segment
            edges.append(Edge(f"{previous_node.id}-{intermediate_node_id}", previous_node, intermediate_node, default_interval))
            previous_node = intermediate_node

        edges.append(Edge(f"{previous_node.id}-{end_node.id}", previous_node, end_node, travel_time % default_interval))

    return nodes, edges, segments, node2segments

def calc_coordinates_with_networkx(nodes, edges):
    G = nx.Graph()

    # Add nodes to the graph
    for node_id, node in nodes.items():
        G.add_node(node_id, weight=node.weight)

    # Add edges to the graph
    for edge in edges:
        G.add_edge(edge.start_node.id, edge.end_node.id, weight=edge.weight)

    # Calculate the coordinates using networkx layout
    pos = nx.spring_layout(G, scale=2)

    # Update node coordinates
    for node_id, (x, y) in pos.items():
        nodes[node_id].x = x
        nodes[node_id].y = y

    return nodes

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
        LineSegment(d2, s26),
        LineSegment(s26, s25),
        LineSegment(s25, s24),
        LineSegment(s24, s23),
        LineSegment(s23, s22),
        LineSegment(s22, s21),
        LineSegment(s21, d1)
    ]

    platforms = [d1, s11, s12, s13, s14, s15, s16, d2, s21, s22, s23, s24, s25, s26]

    nodes, edges = build_topology(platforms, line_segments)
    nodes = calc_coordinates_with_networkx(nodes, edges)

    for node_id, node in nodes.items():
        print(f"Node {node_id}: ({node.x}, {node.y})")