import math
from heapq import heappop, heappush
from utils.sheets.LocalSheetUtils import LocalSheetUtils

class PathfindingUtils:
    def __init__(self):
        self.local_sheet_utils = LocalSheetUtils()

    def retrieve_digital_map(self):
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Map")

        # Extract the column headings from the first row
        column_headings = sheet_values[0]
        sheet_values = sheet_values[1:]  # Remove the headings from the data
        
        # Convert rows into a list of dictionaries
        map_data = []
        for row in sheet_values:
            row_dict = {column_headings[i]: row[i] for i in range(len(column_headings))}
            map_data.append(row_dict)

        return map_data  # No need to return as JSON unless required

    # Heuristic function: straight-line distance between two hexes
    def heuristic(self, hex1, hex2):
        x1, y1 = self.hex_to_coordinates(hex1)
        x2, y2 = self.hex_to_coordinates(hex2)
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # A* Pathfinding Algorithm
    def a_star(self, movement_type, start, goal, hexes, avoid):
        hex_map = {hex['Hex']: hex for hex in hexes}
        
        # Translate avoid list into hex IDs
        avoid_hexes = set()
        for hex_data in hexes:
            if hex_data['Hex'] in avoid or hex_data.get('Holding Name') in avoid:
                avoid_hexes.add(hex_data['Hex'])
        
        open_set = []
        heappush(open_set, (0, start))  # (priority, hex)
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        
        while open_set:
            _, current = heappop(open_set)
            
            if current == goal:
                return self.reconstruct_path(came_from, current)
            
            neighbors = self.get_neighbors(movement_type, current, hex_map, avoid_hexes)
            for neighbor in neighbors:
                terrain_cost = self.terrain_movement_cost(movement_type, hex_map[neighbor])
                tentative_g_score = g_score[current] + terrain_cost
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heappush(open_set, (f_score[neighbor], neighbor))
        
        return None  # No path found

    # Reconstruct the path from the came_from dictionary
    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    # Determine movement cost based on terrain, with special rules for Mountains
    def terrain_movement_cost(self, movement_type, hex_data):
        terrain = hex_data['Terrain']
        has_road = hex_data.get('Road', False)
        has_holding = hex_data.get('Holding', False)

        if movement_type == "army":
            if terrain == "Mountains":
                # Mountain is passable if it has either a Road or a Holding
                return 3 if has_road or has_holding else float('inf')
            if terrain == "Sea":
                return float('inf')  # Sea is impassable for army
            # Cost for other terrains
            terrain_costs = {"Hills": 2, "Swamp": 4, "Desert": 3}
            return terrain_costs.get(terrain, 1)  # Default cost for other terrains

        if movement_type == "fleet" and terrain == "Sea":
            return 1
        return float('inf')  # Non-sea is impassable by ship

    # Get the neighbors of a hex, considering avoid list
    def get_neighbors(self, movement_type, hex_id, hex_map, avoid_hexes):
        col, row = hex_id[0], int(hex_id[1:])
        neighbors = []
        
        # Direction offsets for odd and even columns
        odd_offsets = [(-1, 1), (0, -1), (-1, 0), (1, 0), (0, 1), (1, 1)]
        even_offsets = [(-1, 0), (0, -1), (-1, -1), (1, -1), (0, 1), (1, 0)]
        
        # Determine if the column is odd or even
        column_index = ord(col) - ord('A')
        offsets = odd_offsets if column_index % 2 != 0 else even_offsets
        
        # Check all possible neighbors
        for dx, dy in offsets:
            neighbor_col = chr(ord(col) + dx)
            neighbor_row = row + dy
            neighbor_id = f"{neighbor_col}{neighbor_row}"
            
            # Check if the neighbor exists
            if neighbor_id in hex_map:
                # Skip neighbors in the avoid list
                if neighbor_id in avoid_hexes:
                    print(f"Skipping {neighbor_id} because it's in the avoid list.")
                    continue
                
                neighbor_data = hex_map[neighbor_id]
                
                # Ensure it's not impassable based on terrain
                if self.terrain_movement_cost(movement_type, neighbor_data) != float('inf'):
                    neighbors.append(neighbor_id)
                else:
                    print(f"Skipping {neighbor_id} because terrain is impassable.")
        
        return neighbors

    # Convert hex IDs to numerical coordinates for distance calculations
    def hex_to_coordinates(self, hex_id):
        col, row = hex_id[0], int(hex_id[1:])
        column_index = ord(col) - ord('A')
        return column_index, row

    def retrieve_movement_path(self, movement_type, start, goal, avoid):
        hexes = self.retrieve_digital_map()

        # Ensure avoid is a list (or empty list if None)
        if avoid is None:
            avoid = []

        avoid_hexes = set()
        start_hex = None
        goal_hex = None

        # Check if start and goal are Hex IDs
        for hex_data in hexes:
            if start == hex_data['Hex']:
                start_hex = start  # Start is already a Hex ID
            elif hex_data.get('Holding Name') == start:
                start_hex = hex_data['Hex']  # Start resolved from Holding Name
            
            if goal == hex_data['Hex']:
                goal_hex = goal  # Goal is already a Hex ID
            elif hex_data.get('Holding Name') == goal:
                goal_hex = hex_data['Hex']  # Goal resolved from Holding Name
            
            # Populate avoid_hexes
            for avoid_item in avoid:
                if avoid_item == hex_data['Hex'] or hex_data.get('Holding Name') == avoid_item:
                    avoid_hexes.add(hex_data['Hex'])

        # Debugging information
        print(f"Resolved Start Hex: {start_hex}, Goal Hex: {goal_hex}, Avoid Hexes: {avoid_hexes}")

        # Verify start and goal
        if not start_hex or not goal_hex:
            print("Invalid start or goal Hex or Holding Name.")
            return None

        # Run the A* algorithm
        path = self.a_star(movement_type.lower(), start_hex, goal_hex, hexes, avoid_hexes)
        
        if path:
            print("Path found:", path)
        else:
            print("No path found.")
        
        return path
