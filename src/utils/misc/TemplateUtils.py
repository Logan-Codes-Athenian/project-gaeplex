import re

class TemplateUtils:
    def __init__(self):
        pass

    def parse_movement_template(self, template):
        pattern = re.compile(
            r"Player:\s*(?P<player><@[\d]+>)\s*"
            r"Army ID:\s*(?P<army_id>\d+_\d+)\s*"
            r"To:\s*(?P<destination>[A-Z]+\d+|[A-Za-z ]+)\s*"  
            r"Intentions:\s*(?P<intent>[^\n]+)\s*"
            r"Avoid:\s*(?P<avoid>[^\n]+)\s*"
            r"Arrival Message:\s*(?P<arrival>.+)\s*"
            r"Departure Message:\s*(?P<departure>.+)\s*"
        )

        match = pattern.search(template)
        
        if match:
            return {
                "player": match.group("player"),
                "army_id": match.group("army_id"),
                "destination": match.group("destination"),
                "intent": match.group("intent"),
                "avoid": match.group("avoid").split(", "),
                "arrival": match.group("arrival"),
                "departure": match.group("departure")
            }
        else:
            raise ValueError("The provided template does not match the expected format.")
        
    def parse_army_template(self, template):
        pattern = re.compile(
            r"Player:\s*(?P<player><@[\d]+>)\s*"  
            r"Current Hex:\s*(?P<current>[A-Z]+\d+|[A-Za-z]+)\s*"
            r"Commanders:\s*(?P<commanders>[^\n]+)\s*"
            r"Troops:\s*(?P<troops>[^\n]+)\s*"
            r"Navy:\s*(?P<navy>[^\n]+)\s*"
            r"Siege:\s*(?P<siege>[^\n]+)\s*"
        )

        match = pattern.search(template)
        
        if match:
            return {
                "player": match.group("player"),
                "current": match.group("current"),
                "commanders": match.group("commanders").split(", "),
                "troops": match.group("troops").split(", "),
                "navy": match.group("navy").split(", "),
                "siege": match.group("siege").split(", ")
            }
        else:
            raise ValueError("The provided template does not match the expected format.")
        
    def parse_custom_season_template(self, template):
        pattern = re.compile(
            r"Army:\s*(?P<army>\d+)\s*"
            r"Army with Siege:\s*(?P<siege>\d+)\s*"
            r"Naval movement:\s*(?P<naval>\d+)\s*"
            r"Cavalry Only:\s*(?P<cavalry>\d+)\s*"
        )

        match = pattern.search(template)
        
        if match:
            return {
                "army": match.group("army"),
                "siege": match.group("siege"),
                "naval": match.group("naval"),
                "cavalry": match.group("cavalry")
            }
        else:
            raise ValueError("The provided template does not match the expected format.")

