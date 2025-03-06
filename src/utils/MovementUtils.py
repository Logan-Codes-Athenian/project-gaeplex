class MovementUtils:
    def __init__(self):
        pass

    def get_minutes_per_hex(self, movement):
        # Determine base minutes per hex based on composition.
        print(f"get_minutes_per_hex for:\n{movement}")

        print(movement.get("navy"))

        # Check if navy is not equal to ['None']
        if movement.get("navy") != ['None']:
            print(30)
            return 30
        
        # Since army is already a list, no need to split
        army_units = movement.get("army", [])
        print(f"Army Units:\n{army_units}")
        cav_terms = {"cavalry", "cav", "upstart noble band", "frankish knights"}
        
        # Check if army is not empty and all elements are cavalry-related
        cav_only = bool(army_units) and all(
            any(cav in unit.lower() for cav in cav_terms) for unit in army_units
        )
        print(f"Cav Only: {cav_only}")
        
        if cav_only and movement.get("siege") == ['None']:
            print(15)
            return 15
        elif movement.get("siege") != ['None']:
            print(60)
            return 60
        else:
            print(30)
            return 30
