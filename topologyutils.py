from topology.route import Route
from functools import lru_cache
from logger import logger

@lru_cache(maxsize=128)
def get_possible_routes(env, start_node, look_forward):
    """
    Find all possible routes from a starting node up to a specified depth
    
    Args:
        env (Environment): The environment containing topology information
        start_node (Node): Starting node for route generation
        look_forward (int): Number of nodes to look ahead
        
    Returns:
        list[Route]: List of all possible routes from start_node
    
    Usage example:
        # Get all possible routes looking 3 nodes ahead
        start_node = env.get_node(1)  # Starting from node 1
        routes = get_possible_routes(env, start_node, 3)

        # Print the routes
        print_routes(routes)
    
    Example output:
        Found 4 possible routes:
        Route R-1-2-3:
        Path: 1 -> 2 -> 3 -> 4
        Length: 4 nodes

        Route R-1-2-5:
        Path: 1 -> 2 -> 5 -> 6
        Length: 4 nodes

        Route R-1-7-8:
        Path: 1 -> 7 -> 8 -> 9
        Length: 4 nodes

        Route R-1-7-10:
        Path: 1 -> 7 -> 10 -> 11
        Length: 4 nodes
    """
    @lru_cache(maxsize=128)
    def _build_routes_recursive(current_node, current_route, depth, routes):
        """
        Recursively build all possible routes
        
        Args:
            current_node (Node): Current node being processed
            current_route (Route): Route being built
            depth (int): Remaining depth to explore
            routes (list[Route]): Collection of routes being built
        """
        if depth == 0:
            routes.append(current_route)
            return
            
        # Get all possible next nodes
        next_nodes = env.get_next_nodes(current_node)
        
        for next_node in next_nodes:
            # Find connecting edge
            connecting_edge = None
            for edge in env.edges:
                if ((edge.start_node.id == current_node and edge.end_node.id == next_node) or
                    (edge.start_node.id == next_node and edge.end_node.id == current_node)):
                    connecting_edge = edge
                    break
                    
            if connecting_edge:
                # Create new route branch
                new_route = Route(f"{current_route.id}-{next_node}")
                
                # Copy existing route nodes and edges
                new_route.nodes = current_route.nodes.copy()
                new_route.edges = current_route.edges.copy()
                
                # Add new node and edge
                new_route.add_node(env.get_node(next_node), connecting_edge)
                
                # Continue building this route branch
                _build_routes_recursive(next_node, new_route, depth - 1, routes)
    
    # Initialize collection of routes
    possible_routes = []
    
    # Create initial route with start node
    initial_route = Route(f"R-{start_node.id}")
    initial_route.nodes.append(start_node)
    
    # Build all possible routes recursively
    _build_routes_recursive(start_node.id, initial_route, look_forward, possible_routes)
    
    return possible_routes

def print_routes(routes):
    """
    Helper function to print routes in a readable format
    
    Args:
        routes (list[Route]): List of routes to print
    """
    print(f"\nFound {len(routes)} possible routes:")
    for route in routes:
        print(f"Route {route.id}:")
        path = " -> ".join(str(node.id) for node in route.nodes)
        print(f"  Path: {path}")
        print(f"  Length: {len(route.nodes)} nodes")
        print()

def node_in_segment_percentage(node, segment, segment2nodes):
    """
    Calculate the percentage of a node's presence in a segment
    
    Args:
        node (Node): The node to check
        segment (str): The segment identifier
        segment2nodes (dict): Dictionary mapping segment identifiers to lists of nodes
        
    Returns:
        float: Percentage of the node's presence in the segment
    """
    if segment not in segment2nodes:
        return 0
    
    nodes_in_segment = segment2nodes[segment]
    if node == nodes_in_segment[0]:
        return 0
    if node == nodes_in_segment[-1]:
        return 1
    intermediate_nodes = nodes_in_segment[1:-1]
    total_weight = sum(node.weight for node in intermediate_nodes)
    
    if total_weight == 0:
        return 0
    
    # sum the weight of the nodes in the segment until the given node
    cumulative_weight = 0
    for n in intermediate_nodes:
        cumulative_weight += n.weight
        if n.id == node.id:
            break
        
    return (cumulative_weight / total_weight) 