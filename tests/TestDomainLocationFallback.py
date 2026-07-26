import unittest

from ok.feature.Box import Box
from ok.task.exceptions import CannotFindException
from src.task.CharacterMaterialTask import CharacterMaterialTask
from src.task.DomainTask import DomainTask
from src.task.ForgeryTask import ForgeryTask
from src.task.TacetTask import TacetTask


class TestDomainLocationFallback(unittest.TestCase):
    def test_character_material_entry_uses_visible_forward_key_presses(self):
        calls = []
        f_checks = iter([False, False, True])

        class Task:
            DOMAIN_ENTRY_READY_DELAY = (
                CharacterMaterialTask.DOMAIN_ENTRY_READY_DELAY
            )
            DOMAIN_ENTRY_FORWARD_TIME = (
                CharacterMaterialTask.DOMAIN_ENTRY_FORWARD_TIME
            )
            DOMAIN_ENTRY_BACKWARD_TIME = (
                CharacterMaterialTask.DOMAIN_ENTRY_BACKWARD_TIME
            )
            DOMAIN_ENTRY_KEY_PULSE = (
                CharacterMaterialTask.DOMAIN_ENTRY_KEY_PULSE
            )

            def log_info(self, message):
                calls.append(('info', message))

            def log_error(self, message):
                calls.append(('error', message))

            def sleep(self, duration):
                calls.append(('sleep', duration))

            def find_f_with_text(self):
                calls.append(('find_f',))
                return next(f_checks)

            def middle_click(self, after_sleep):
                calls.append(('middle_click', after_sleep))

            def send_key(self, key, down_time, after_sleep):
                calls.append(('send_key', key, down_time, after_sleep))

            def screenshot(self, name):
                calls.append(('screenshot', name))

        found = DomainTask.walk_to_domain_interaction(Task())

        self.assertTrue(found)
        self.assertIn(('sleep', 3), calls)
        self.assertIn(('send_key', 'w', 0.25, 0.05), calls)
        self.assertNotIn(('screenshot', 'domain_entry_f_not_found'), calls)

    def test_domain_entry_saves_screenshot_after_forward_search_failure(self):
        calls = []

        class Task:
            DOMAIN_ENTRY_READY_DELAY = 0
            DOMAIN_ENTRY_FORWARD_TIME = 0.5
            DOMAIN_ENTRY_BACKWARD_TIME = 0
            DOMAIN_ENTRY_KEY_PULSE = 0.25

            def log_info(self, message):
                calls.append(('info', message))

            def log_error(self, message):
                calls.append(('error', message))

            def find_f_with_text(self):
                return False

            def middle_click(self, after_sleep):
                calls.append(('middle_click', after_sleep))

            def send_key(self, key, down_time, after_sleep):
                calls.append(('send_key', key, down_time, after_sleep))

            def screenshot(self, name):
                calls.append(('screenshot', name))

        with self.assertRaises(CannotFindException):
            DomainTask.walk_to_domain_interaction(Task())

        self.assertEqual(
            2,
            len([call for call in calls if call[0] == 'send_key']),
        )
        self.assertIn(('screenshot', 'domain_entry_f_not_found'), calls)

    def test_forgery_candidates_keep_the_same_material_slot(self):
        self.assertEqual(
            [1, 6],
            ForgeryTask.same_material_candidates(1, [5, 5, 5, 5]),
        )
        self.assertEqual(
            [7, 2],
            ForgeryTask.same_material_candidates(7, [5, 5, 5, 5]),
        )
        self.assertEqual(
            [12, 17],
            ForgeryTask.same_material_candidates(12, [5, 5, 5, 5]),
        )
        self.assertEqual(
            [18, 13],
            ForgeryTask.same_material_candidates(18, [5, 5, 5, 5]),
        )

    def test_forgery_falls_back_only_to_same_material(self):
        calls = []

        class Task:
            structure = [5, 5, 5, 5]
            total_number = 20

            same_material_candidates = staticmethod(
                ForgeryTask.same_material_candidates
            )

            def open_boss_book(self, name):
                calls.append(('open_boss_book', name))

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def enter_book_domain_target(self, serial, total, structure):
                calls.append(('enter', serial, total, structure))
                return serial == 6

            def leave_unavailable_domain_page(self):
                calls.append(('leave',))
                return True

            def log_info(self, message):
                calls.append(('log_info', message))

        ForgeryTask.teleport_into_domain(Task(), 1)

        attempted = [call[1] for call in calls if call[0] == 'enter']
        self.assertEqual([1, 6], attempted)
        self.assertNotIn(2, attempted)
        self.assertEqual(1, calls.count(('leave',)))

    def test_locked_map_does_not_click_team_challenge(self):
        calls = []

        class Task:
            teleport_timeout = 100
            finish_domain_destination = DomainTask.finish_domain_destination

            def click_on_book_target(self, serial, total, structure):
                calls.append(('select', serial))
                return False

            def wait_until(self, action, **kwargs):
                calls.append(('travel',))
                return True

            def click_traval_button(self):
                raise AssertionError('the test wait stub does not invoke actions')

            def wait_feature(self, name, **kwargs):
                calls.append(('wait_feature', name))
                return None

            def find_one(self, name, threshold):
                return object() if name == 'gray_teleport' else None

            def log_info(self, message):
                calls.append(('log_info', message))

            def click_team_challenge(self):
                calls.append(('team_challenge',))

        entered = DomainTask.enter_book_domain_target(
            Task(), 1, 20, [5, 5, 5, 5]
        )

        self.assertFalse(entered)
        self.assertNotIn(('team_challenge',), calls)

    def test_unavailable_map_can_require_two_back_attempts(self):
        calls = []

        class Task:
            guidebook_checks = 0

            def back(self, after_sleep):
                calls.append(('back', after_sleep))

            def wait_guidebook_page(self, time_out):
                self.guidebook_checks += 1
                return self.guidebook_checks == 2

            def in_team_and_world(self):
                return False

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

        returned = DomainTask.leave_unavailable_domain_page(Task())

        self.assertTrue(returned)
        self.assertEqual(2, calls.count(('back', 1)))

    def test_current_solo_challenge_button_uses_ocr_fallback(self):
        calls = []
        template_calls = 0
        solo_button = Box(
            1570,
            950,
            280,
            65,
            name='单人挑战',
        )

        class Task:
            def wait_click_feature(self, feature, **kwargs):
                nonlocal template_calls
                template_calls += 1
                calls.append(('template', feature, kwargs))
                return template_calls == 2

            def wait_ocr(self, *box, **kwargs):
                calls.append(('ocr', box, kwargs))
                return [solo_button]

            def log_info(self, message):
                calls.append(('info', message))

            def click_box(self, box, after_sleep):
                calls.append(('click', box.name, after_sleep))

            def screenshot(self, name):
                calls.append(('screenshot', name))

        clicked = DomainTask.click_team_challenge(Task())

        self.assertTrue(clicked)
        self.assertIn(('click', '单人挑战', 1), calls)
        self.assertEqual(2, template_calls)
        self.assertNotIn(('screenshot', 'solo_challenge_not_found'), calls)

    def test_team_page_start_challenge_can_use_ocr_fallback(self):
        calls = []
        ocr_calls = 0
        solo_button = Box(1570, 950, 280, 65, name='单人挑战')
        start_button = Box(1570, 950, 280, 65, name='开始挑战')

        class Task:
            def wait_click_feature(self, feature, **kwargs):
                calls.append(('template', feature, kwargs))
                return False

            def wait_ocr(self, *box, **kwargs):
                nonlocal ocr_calls
                ocr_calls += 1
                calls.append(('ocr', box, kwargs))
                return [solo_button] if ocr_calls == 1 else [start_button]

            def log_info(self, message):
                calls.append(('info', message))

            def click_box(self, box, after_sleep):
                calls.append(('click', box.name, after_sleep))

            def screenshot(self, name):
                calls.append(('screenshot', name))

        clicked = DomainTask.click_team_challenge(Task())

        self.assertTrue(clicked)
        self.assertEqual(
            [
                ('click', '单人挑战', 1),
                ('click', '开始挑战', 1),
            ],
            [call for call in calls if call[0] == 'click'],
        )
        self.assertNotIn(
            ('screenshot', 'team_start_challenge_not_found'),
            calls,
        )

    def test_tacet_reopens_same_category_and_tries_next_location(self):
        calls = []

        class Task:
            total_number = 19
            structure = [2, 5, 5, 7]
            order_material_locations = staticmethod(
                DomainTask.order_material_locations
            )

            def build_material_page_dictionary(self, category):
                calls.append(('build_dictionary', category))
                return {'locations': []}

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def enter_book_domain_target(self, serial, total, structure):
                calls.append(('enter', serial))
                return serial == 2

            def leave_unavailable_domain_page(self):
                calls.append(('leave',))
                return True

            def open_boss_book(self, category):
                calls.append(('open_boss_book', category))

            def log_info(self, message):
                calls.append(('log_info', message))

        entered = TacetTask.teleport_to_tacet(Task(), 0)

        self.assertTrue(entered)
        self.assertEqual([1, 2], [
            call[1] for call in calls if call[0] == 'enter'
        ])
        self.assertEqual([('open_boss_book', 'wuyin')], [
            call for call in calls if call[0] == 'open_boss_book'
        ])
        self.assertEqual(1, calls.count(('leave',)))

    def test_material_locations_prioritize_direct_challenge(self):
        locations = [
            {'name': 'locked-a', 'is_direct': False},
            {'name': 'direct-b', 'is_direct': True},
            {'name': 'locked-c', 'is_direct': False},
        ]

        ordered = DomainTask.order_material_locations(
            locations,
            preferred_index=0,
        )

        self.assertEqual(
            ['direct-b', 'locked-a', 'locked-c'],
            [location['name'] for location in ordered],
        )

    def test_material_location_order_rotates_from_configured_index(self):
        locations = [
            {'name': 'a', 'is_direct': False},
            {'name': 'b', 'is_direct': False},
            {'name': 'c', 'is_direct': False},
        ]

        ordered = DomainTask.order_material_locations(
            locations,
            preferred_index=1,
        )

        self.assertEqual(
            ['b', 'c', 'a'],
            [location['name'] for location in ordered],
        )


if __name__ == '__main__':
    unittest.main()
