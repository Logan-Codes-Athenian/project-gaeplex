import math
import pandas as pd
from heapq import heappop, heappush
from utils.sheets.LocalSheetUtils import LocalSheetUtils

class PathfindingUtils:
    def __init__(self):
        self.local_sheet_utils = LocalSheetUtils()

    def retrieve_digital_map(self):
        try:
            df = self.local_sheet_utils.get_sheet_by_name("Map")
            if df is None or df.empty:
                print("Error: Map is empty or missing.")
                return []
            # Convert the DataFrame to a list of dictionaries
            map_data = df.to_dict(orient='records')
            return map_data
        except Exception as e:
            print(f"Error reading the map: {e}")
            return []

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
                return self.reconstruct_path(came_from, current), self.extract_terrain_values(came_from, current, hex_map, movement_type)
            
            neighbors = self.get_neighbors(movement_type, current, hex_map, avoid_hexes)
            for neighbor in neighbors:
                terrain_cost = self.terrain_movement_cost(movement_type, hex_map[neighbor])
                tentative_g_score = g_score[current] + terrain_cost
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heappush(open_set, (f_score[neighbor], neighbor))
        
        return None, None  # No path found

    # Reconstruct the path from the came_from dictionary
    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    # Extract terrain values for the path
    def extract_terrain_values(self, came_from, current, hex_map, movement_type):
        path = self.reconstruct_path(came_from, current)
        return [self.terrain_movement_cost(movement_type, hex_map[hex_id]) for hex_id in path]

    # Determine movement cost based on terrain, with special rules for Mountains and The Wall
    def terrain_movement_cost(self, movement_type, hex_data):
        terrain = hex_data["Terrain"]
        print(hex_data)
        has_road = hex_data.get("Road", False)
        has_river = hex_data.get("River", False)
        has_holding = hex_data.get("Holding Name", False)
        print(f"road: {has_road}, river {has_river}, holding {has_holding}")

        if movement_type == "army":
            if has_river == True and (has_road == False and has_holding == False):
                return float('inf')
            if terrain == "Mountains" or terrain == "The Wall":
                return 3 if has_road or has_holding else float('inf')
            if terrain == "Sea":
                return float('inf')
            terrain_costs = {"Hills": 2, "Swamp": 4, "Desert": 3, 
                             "Forest": 3, "Dense Forest": 4, "Snow": 3,
                             "Snowy Forest": 4, "Plains": 1, "Coast": 1, 
                             "Island": 1, "Peninsula": 1}
            return terrain_costs.get(terrain, 1)

        if movement_type == "fleet" and terrain in ["Sea", "Coast", "Island", "Peninsula"]:
            return 1
        return float('inf')

    # Get the neighbors of a hex, considering avoid list
    def get_neighbors(self, movement_type, hex_id, hex_map, avoid_hexes):
        col_part, row_part = self.split_hex_id(hex_id)
        row = int(row_part)
        neighbors = []
        
        column_index = self.column_to_index(col_part)
        
        # Hex grid movement offsets based on column parity
        offsets = [
            (-1, 0), (1, 0),  # Left, Right
            (0, -1), (0, 1),  # Top, Bottom
            (-1, 1) if column_index % 2 == 0 else (-1, -1),  # Top-left / Bottom-left
            (1, 1) if column_index % 2 == 0 else (1, -1),  # Top-right / Bottom-right
        ]
        
        for dx, dy in offsets:
            neighbor_col = self.index_to_column(column_index + dx)
            neighbor_row = row + dy
            neighbor_id = f"{neighbor_col}{neighbor_row:02d}"  # Ensure row is two digits
            
            if neighbor_id in hex_map and neighbor_id not in avoid_hexes:
                neighbor_hex = hex_map[neighbor_id]
                terrain_cost = self.terrain_movement_cost(movement_type, neighbor_hex)

                if terrain_cost == float('inf'):
                    continue

                # Prevent direct fleet movement through Peninsulas
                if movement_type == "fleet":
                    current_terrain = hex_map[hex_id]["Terrain"]
                    neighbor_terrain = neighbor_hex["Terrain"]

                    if current_terrain == "Peninsula" or neighbor_terrain == "Peninsula":
                        # Block fleet travel between coast/water via Peninsula
                        if (current_terrain in ["Sea", "Coast", "Island", "Peninsula"] and 
                            neighbor_terrain in ["Sea", "Coast", "Island", "Peninsula"]):
                            continue  # Disallow direct hop through/into peninsula tile

                neighbors.append(neighbor_id)
        
        return neighbors

    # Convert hex IDs to numerical coordinates for distance calculations
    def hex_to_coordinates(self, hex_id):
        col_part, row_part = self.split_hex_id(hex_id)
        column_index = self.column_to_index(col_part)
        row = int(row_part)
        return column_index, row

    # Split hex ID into column part and row part
    def split_hex_id(self, hex_id):
        # Split into column (letters) and row (digits)
        col_part = ''
        row_part = ''
        for char in hex_id:
            if char.isalpha():
                col_part += char
            else:
                row_part += char
        return col_part, row_part

    # Convert column letters to index (e.g., A=0, B=1, ..., Z=25, AA=26, AB=27, etc.)
    def column_to_index(self, col_part):
        index = 0
        for i, char in enumerate(reversed(col_part)):
            index += (ord(char.upper()) - ord('A') + 1) * (26 ** i)
        return index - 1  # Subtract 1 to make A=0, B=1, etc.

    # Convert index to column letters (e.g., 0=A, 1=B, ..., 25=Z, 26=AA, 27=AB, etc.)
    def index_to_column(self, index):
        col_part = ''
        while index >= 0:
            col_part = chr(ord('A') + (index % 26)) + col_part
            index = (index // 26) - 1
        return col_part

    def retrieve_movement_path(self, movement_type, start, goal, avoid):
        hexes = self.retrieve_digital_map()

        if avoid is None:
            avoid = []

        avoid_hexes = set()
        start_hex = None
        goal_hex = None

        for hex_data in hexes:
            if start == hex_data['Hex']:
                start_hex = start
            elif hex_data.get('Holding Name') == start:
                start_hex = hex_data['Hex']
            
            if goal == hex_data['Hex']:
                goal_hex = goal
            elif hex_data.get('Holding Name') == goal:
                goal_hex = hex_data['Hex']
            
            for avoid_item in avoid:
                if avoid_item == hex_data['Hex'] or hex_data.get('Holding Name') == avoid_item:
                    avoid_hexes.add(hex_data['Hex'])

        if not start_hex or not goal_hex:
            print("Invalid start or goal Hex or Holding Name.")
            return None, None

        path, terrain_values = self.a_star(movement_type.lower(), start_hex, goal_hex, hexes, avoid_hexes)

        if path:
            print("Path found:", path)
            print("Terrain values:", terrain_values)
        else:
            print("No path found.")

        return path, terrain_values