import unittest
from templates import CAVALRY
from src.utils.MovementUtils import MovementUtils
from src.utils.misc.TemplateUtils import TemplateUtils

class TestMovementUtils(unittest.TestCase):
    def setUp(self):
        self.movement_utils = MovementUtils()
        self.template_utils = TemplateUtils()

    def test_cav_only_mins_per_hex(self):
        movement = self.template_utils.parse_movement_template(CAVALRY)

        expected_minutes_per_hex = 15
        actual_minutes_per_hex = self.movement_utils.get_minutes_per_hex(movement)

        self.assertEquals(expected_minutes_per_hex, actual_minutes_per_hex)