import time
import unittest

import numpy as np

from src.char.BaseChar import BaseChar, CharType
from src.task.AutoCombatTask import AutoCombatTask
from src.task.BaseCombatTask import (
    BaseCombatTask,
    NotInCombatException,
    con_colors,
)


class TestCombatSwitch(unittest.TestCase):
    def test_sparse_segmented_concerto_ring_detection(self):
        image = np.zeros((63, 63, 3), dtype=np.uint8)
        center = 31
        for angle in np.linspace(0, 2 * np.pi, 32, endpoint=False):
            x = round(center + 25 * np.cos(angle))
            y = round(center + 25 * np.sin(angle))
            image[y, x] = (90, 115, 215)

        self.assertTrue(
            BaseCombatTask.is_sparse_con_ring_full(
                image,
                con_colors[2],
            )
        )

        partial = np.zeros_like(image)
        for angle in np.linspace(0, np.pi, 14, endpoint=False):
            x = round(center + 25 * np.cos(angle))
            y = round(center + 25 * np.sin(angle))
            partial[y, x] = (90, 115, 215)
        self.assertFalse(
            BaseCombatTask.is_sparse_con_ring_full(
                partial,
                con_colors[2],
            )
        )

    def test_material_style_switch_waits_for_full_concerto(self):
        class Task:
            def get_current_con(self):
                return 0

        task = Task()
        combat = AutoCombatTask.__new__(AutoCombatTask)
        current = BaseChar(task, 0, char_type=CharType.MAIN_DPS)
        target = BaseChar(task, 1, char_type=CharType.HEALER)
        combat.chars = [current, target]
        combat.update_lib_portrait_icon = lambda: None
        combat.wait_for_full_con_before_switch = lambda: True
        attacks = []
        current.continues_normal_attack = (
            lambda duration, **kwargs: attacks.append((duration, kwargs))
        )
        sent_keys = []
        combat.send_key = sent_keys.append

        combat.switch_next_char(current)

        self.assertEqual([], sent_keys)
        self.assertEqual(
            [(0.35, {'until_con_full': True})],
            attacks,
        )

    def test_material_style_switch_rejects_one_frame_full_false_positive(self):
        class Task:
            def get_current_con(self):
                return 1

        task = Task()
        combat = AutoCombatTask.__new__(AutoCombatTask)
        current = BaseChar(task, 0, char_type=CharType.MAIN_DPS)
        target = BaseChar(task, 1, char_type=CharType.HEALER)
        combat.chars = [current, target]
        combat.update_lib_portrait_icon = lambda: None
        combat.wait_for_full_con_before_switch = lambda: True
        combat.sleep = lambda *args, **kwargs: None
        combat.next_frame = lambda: None
        combat.get_current_con = lambda: 0
        attacks = []
        current.continues_normal_attack = (
            lambda duration, **kwargs: attacks.append((duration, kwargs))
        )
        sent_keys = []
        combat.send_key = sent_keys.append

        combat.switch_next_char(current)

        self.assertEqual([], sent_keys)
        self.assertEqual(
            [(0.35, {'until_con_full': True})],
            attacks,
        )

    def test_switch_tolerates_transient_missing_team_ui(self):
        class Task:
            def time_elapsed_accounting_for_freeze(
                    self,
                    start,
                    intro_motion_freeze=False,
            ):
                if start < 0:
                    return 10000
                return time.time() - start

            def get_current_con(self):
                return 0

            def is_con_full(self):
                return False

        task = Task()
        combat = AutoCombatTask.__new__(AutoCombatTask)
        current = BaseChar(task, 0, char_type=CharType.MAIN_DPS)
        target = BaseChar(task, 1, char_type=CharType.HEALER)
        combat.chars = [current, target]
        combat.in_liberation = False
        combat.switch_char_time_out = 5
        combat.update_lib_portrait_icon = lambda: None
        combat.check_combat = lambda: None
        combat.log_debug = lambda *args, **kwargs: None
        combat.click = lambda: None
        combat.sleep = lambda *args, **kwargs: None
        combat.next_frame = lambda: None
        combat.add_freeze_duration = lambda *args, **kwargs: None
        current.f_break = lambda **kwargs: None
        sent_keys = []
        team_states = iter([
            (True, current.index, 2),
            (False, -1, 1),
            (True, target.index, 2),
            (True, target.index, 2),
        ])
        combat.in_team = lambda: next(team_states)
        combat.send_key = lambda key: sent_keys.append(key)
        unexpected_errors = []
        combat.raise_not_in_combat = unexpected_errors.append

        combat.switch_next_char(current)

        self.assertEqual([target.index + 1], sent_keys)
        self.assertEqual([], unexpected_errors)
        self.assertTrue(target.is_current_char)

    def test_switch_still_fails_when_team_ui_stays_missing(self):
        class Task:
            def time_elapsed_accounting_for_freeze(
                    self,
                    start,
                    intro_motion_freeze=False,
            ):
                return 0

            def get_current_con(self):
                return 0

            def is_con_full(self):
                return False

        task = Task()
        combat = AutoCombatTask.__new__(AutoCombatTask)
        current = BaseChar(task, 0, char_type=CharType.MAIN_DPS)
        target = BaseChar(task, 1, char_type=CharType.HEALER)
        combat.chars = [current, target]
        combat.in_liberation = False
        combat.switch_char_time_out = -1
        combat.update_lib_portrait_icon = lambda: None
        combat.check_combat = lambda: None
        combat.log_debug = lambda *args, **kwargs: None
        combat.click = lambda: None
        combat.sleep = lambda *args, **kwargs: None
        combat.add_freeze_duration = lambda *args, **kwargs: None
        current.f_break = lambda **kwargs: None
        team_states = iter([
            (True, current.index, 2),
            (False, -1, 1),
        ])
        combat.in_team = lambda: next(team_states)
        combat.send_key = lambda key: None

        def raise_not_in_combat(message):
            raise NotInCombatException(message)

        combat.raise_not_in_combat = raise_not_in_combat

        with self.assertRaisesRegex(
                NotInCombatException,
                'team UI missing too long',
        ):
            combat.switch_next_char(current)


if __name__ == '__main__':
    unittest.main()
