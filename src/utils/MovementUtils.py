class MovementUtils:
    def __init__(self):
        pass

    def get_minutes_per_hex(self, movement):
        # Determine base minutes per hex based on composition.
        if movement.get("navy"):
            return 30
        else:
            army_units = movement.get("army", [])
            army_units_split =  army_units.split(",| ") if army_units != [] else []
            cav_terms = {"cavalry", "cav", "upstart noble band", "frankish knights"}
            
            # Check if army is not empty and all elements are cavalry-related
            cav_only = bool(army_units) and all(
                any(cav in unit.lower() for cav in cav_terms) for unit in army_units_split
                )
            
            if cav_only:
                return 15
            elif movement.get("siege"):
                return 60
            else:
                return 30