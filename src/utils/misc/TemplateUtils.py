import re

class TemplateUtils:
    def __init__(self):
        pass

    def parse_movement_template(self, template):
        pattern = re.compile(
            r"Player:\s*(?P<player><@[\d]+>)\s*"  
            r"To:\s*(?P<destination>[A-Z]\d+|[A-Za-z]+)\s*"  
            r"From:\s*(?P<origin>[A-Z]\d+|[A-Za-z]+)\s*"
            r"Commanders:\s*(?P<commanders>[^\n]+)\s*"
            r"Intentions:\s*(?P<intent>[^\n]+)\s*"
            r"Army:\s*(?P<army>[^\n]+)\s*"
            r"Navy:\s*(?P<navy>[^\n]+)\s*"
            r"Siege:\s*(?P<siege>[^\n]+)\s*"
            r"Avoid:\s*(?P<avoid>[^\n]+)\s*"
            r"Arrival Message:\s*(?P<arrival>.+)\s*"
            r"Departure Message:\s*(?P<departure>.+)\s*"
        )

        match = pattern.search(template)
        
        if match:
            return {
                "player": match.group("player"),
                "origin": match.group("origin"),
                "destination": match.group("destination"),
                "commanders": match.group("commanders").split(", "),
                "intent": match.group("intent"),
                "army": match.group("army").split(", "),
                "navy": match.group("navy").split(", "),
                "siege": match.group("siege").split(", "),
                "avoid": match.group("avoid").split(", "),
                "arrival": match.group("arrival"),
                "departure": match.group("departure")
            }
        else:
            raise ValueError("The provided template does not match the expected format.")
