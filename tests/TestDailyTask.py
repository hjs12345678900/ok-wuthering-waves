import unittest
import re
from unittest.mock import ANY, patch

from ok.feature.Box import Box
from src.task.BaseWWTask import (
    BaseWWTask,
    GUIDEBOOK_MENU_POSITION,
    GUIDEBOOK_TITLE_BOX,
    MATERIALS_GUIDE_POSITION,
    MATERIALS_TITLE_BOX,
)
from src.task.DailyTask import (
    BATTLE_PASS_CLAIM_BOX,
    BATTLE_PASS_ENTRY_TEXT,
    BATTLE_PASS_REWARD_TAB_POSITION,
    BATTLE_PASS_REWARD_TEXT,
    BATTLE_PASS_TASK_TAB_POSITION,
    BATTLE_PASS_TASK_TEXT,
    BATTLE_PASS_TITLE_BOX,
    DAILY_GUIDE_POSITION,
    DAILY_PAGE_TITLE_BOX,
    DAILY_POINTS_BOX,
    DAILY_REWARD_BOX,
    DAILY_REWARD_POSITION,
    DAILY_STAMINA_GO_X,
    DAILY_STAMINA_PROGRESS_BOX,
    DAILY_TASK_CLAIM_BOX,
    MAIL_CLAIM_BOX,
    MAIL_TITLE_BOX,
    TERMINAL_GRID_BOX,
    TERMINAL_MAIL_POSITION,
    TERMINAL_TITLE_BOX,
    DailyTask,
)
from src.task.GardenTask import GardenTask
from src.task.WWOneTimeTask import WWOneTimeTask


class TestDailyTask(unittest.TestCase):
    def test_run_checks_open_daily_page_before_requiring_world(self):
        calls = []

        class Task:
            logged_in = True
            config = {}

            def validate_additional_tasks(self):
                return True

            def open_daily(self):
                calls.append(('open_daily',))
                return None, False

            def ensure_main(self, **_kwargs):
                raise AssertionError('run must not close an already-open daily page')

            def log_error(self, message):
                calls.append(('log_error', message))

        with patch.object(WWOneTimeTask, 'run', return_value=None):
            DailyTask.run(Task())

        self.assertEqual(('open_daily',), calls[0])

    def test_guidebook_shell_uses_top_left_title_ocr(self):
        calls = []

        class Task:
            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                return [Box(102, 52, 110, 33, name='活跃行迹')]

        result = BaseWWTask.wait_guidebook_page(Task(), time_out=4)

        self.assertTrue(result)
        self.assertEqual(GUIDEBOOK_TITLE_BOX, calls[0][1])
        self.assertEqual(4, calls[0][2]['time_out'])

    def test_guidebook_title_does_not_accept_map_location_name(self):
        from src.task.BaseWWTask import GUIDEBOOK_TITLE_TEXT

        self.assertFalse(any(
            pattern.fullmatch('乘霄山')
            for pattern in GUIDEBOOK_TITLE_TEXT
            if isinstance(pattern, re.Pattern)
        ))
        self.assertTrue(any(
            pattern.fullmatch('活跃行迹')
            for pattern in GUIDEBOOK_TITLE_TEXT
            if isinstance(pattern, re.Pattern)
        ))

    def test_open_book_uses_calibrated_menu_position_when_hotkey_misses(self):
        calls = []

        class Task:
            key_config = {'Guidebook Key': 'f2'}

            def reset_to_false(self, name):
                calls.append(('reset_to_false', name))

            def ensure_main(self):
                calls.append(('ensure_main',))

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message, notify=False):
                calls.append(('log_error', message, notify))

            def in_team_and_world(self):
                return True

            def send_key(self, key, after_sleep=0):
                calls.append(('send_key', key, after_sleep))

            def send_key_down(self, key):
                calls.append(('send_key_down', key))

            def send_key_up(self, key):
                calls.append(('send_key_up', key))

            def click_relative(self, x, y):
                calls.append(('click_relative', x, y))

            def wait_book(self, feature):
                calls.append(('wait_book', feature))
                return Box(43, 283, 65, 75, name=feature)

            def click_box(self, box, after_sleep=0):
                calls.append(('click_box', box.name, after_sleep))

            def sleep(self, duration):
                calls.append(('sleep', duration))

        result = BaseWWTask.openF2Book(Task(), 'gray_book_boss')

        self.assertEqual('gray_book_boss', result.name)
        self.assertIn(
            ('click_relative', *GUIDEBOOK_MENU_POSITION),
            calls,
        )

    def test_open_materials_book_uses_current_icon_and_verifies_title(self):
        calls = []

        class Task:
            key_config = {'Guidebook Key': 'f2'}

            def ensure_main(self):
                calls.append(('ensure_main',))

            def log_info(self, message):
                calls.append(('log_info', message))

            def in_team_and_world(self):
                return False

            def send_key_down(self, key):
                calls.append(('send_key_down', key))

            def send_key_up(self, key):
                calls.append(('send_key_up', key))

            def sleep(self, duration):
                calls.append(('sleep', duration))

            def screenshot(self, name):
                calls.append(('screenshot', name))

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                return [Box(67, 32, 85, 30, name='素材获取')]

            def wait_guidebook_page(self, time_out=0):
                calls.append(('wait_guidebook_page', time_out))
                return [Box(67, 32, 85, 30, name='素材获取')]

            def log_error(self, message):
                calls.append(('log_error', message))

        opened = BaseWWTask.open_materials_book(Task())

        self.assertTrue(opened)
        self.assertNotIn(('ensure_main',), calls)
        self.assertIn(
            ('click_relative', MATERIALS_GUIDE_POSITION, {'after_sleep': 1}),
            calls,
        )
        self.assertIn(
            (
                'wait_ocr',
                MATERIALS_TITLE_BOX,
                {
                    'match': ANY,
                    'time_out': 3,
                    'settle_time': 0.5,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )

    def test_open_daily_waits_for_stamina_progress_after_page_animation(self):
        calls = []

        class Task:
            height = 1080

            def open_daily_activity_page(self):
                calls.append(('open_daily_activity_page',))
                return True

            def openF2Book(self, feature):
                calls.append(('openF2Book', feature))

            def click(self, *args, **kwargs):
                calls.append(('click', args, kwargs))

            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                return [Box(438, 562, 70, 24, name='40/180')]

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def get_total_daily_points(self):
                return 80

            def log_info(self, message):
                calls.append(('log_info', message))

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

        current, ready = DailyTask.open_daily(Task())

        self.assertEqual(40, current)
        self.assertFalse(ready)
        self.assertIn(
            (
                'wait_ocr',
                DAILY_STAMINA_PROGRESS_BOX,
                {
                    'match': ANY,
                    'time_out': 3,
                    'settle_time': 0.2,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )
        self.assertIn(
            (
                'click_relative',
                (DAILY_STAMINA_GO_X, 574 / 1080),
                {'name': 'daily_stamina_go', 'after_sleep': 2},
            ),
            calls,
        )

    def test_open_daily_activity_uses_calibrated_first_icon(self):
        calls = []
        page_checks = 0
        world_checks = iter([True, False])

        class Task:
            key_config = {'Guidebook Key': 'f2'}

            def ensure_main(self):
                calls.append(('ensure_main',))

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def in_team_and_world(self):
                return next(world_checks)

            def send_key(self, key, after_sleep=0):
                calls.append(('send_key', key, after_sleep))

            def send_key_down(self, key):
                calls.append(('send_key_down', key))

            def send_key_up(self, key):
                calls.append(('send_key_up', key))

            def sleep(self, duration):
                calls.append(('sleep', duration))

            def screenshot(self, name):
                calls.append(('screenshot', name))

            def wait_guidebook_page(self, time_out=0):
                calls.append(('wait_guidebook_page', time_out))
                return [Box(102, 52, 110, 33, name='活跃行迹')]

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

            def wait_click_ocr(self, *args, **kwargs):
                calls.append(('wait_click_ocr', args, kwargs))
                return [Box(196, 83, 67, 31, name='活跃度')]

            def wait_ocr(self, *args, **kwargs):
                nonlocal page_checks
                calls.append(('wait_ocr', args, kwargs))
                if args == DAILY_STAMINA_PROGRESS_BOX:
                    return []
                page_checks += 1
                if page_checks == 1:
                    return []
                return [Box(14, 32, 110, 31, name='活跃行迹')]

        opened = DailyTask.open_daily_activity_page(Task())

        self.assertTrue(opened)
        self.assertIn(
            (
                'click_relative',
                DAILY_GUIDE_POSITION,
                {'after_sleep': 1, 'name': 'daily_guide_icon'},
            ),
            calls,
        )
        self.assertIn(
            (
                'wait_ocr',
                DAILY_PAGE_TITLE_BOX,
                {
                    'match': ANY,
                    'time_out': 3,
                    'settle_time': 0.5,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )
        self.assertNotIn(
            ('openF2Book', 'gray_book_quest'),
            calls,
        )
        self.assertIn(('screenshot', 'daily/01_before_guidebook'), calls)
        self.assertIn(('screenshot', 'daily/02_after_guidebook'), calls)
        self.assertIn(('screenshot', 'daily/03_after_activity_icon'), calls)
        self.assertIn(('send_key', 'f2', 4), calls)
        self.assertFalse(any(call[0] == 'send_key_down' for call in calls))

    def test_open_daily_activity_does_not_click_sidebar_when_guidebook_failed(self):
        calls = []

        class Task:
            key_config = {'Guidebook Key': 'f2'}

            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                return []

            def ensure_main(self):
                calls.append(('ensure_main',))

            def screenshot(self, name):
                calls.append(('screenshot', name))

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def in_team_and_world(self):
                return False

            def send_key(self, key, after_sleep=0):
                calls.append(('send_key', key, after_sleep))

            def send_key_down(self, key):
                calls.append(('send_key_down', key))

            def send_key_up(self, key):
                calls.append(('send_key_up', key))

            def sleep(self, duration):
                calls.append(('sleep', duration))

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

            def wait_guidebook_page(self, time_out=0):
                calls.append(('wait_guidebook_page', time_out))
                return None

        opened = DailyTask.open_daily_activity_page(Task())

        self.assertFalse(opened)
        self.assertNotIn(
            (
                'click_relative',
                DAILY_GUIDE_POSITION,
                {'after_sleep': 1, 'name': 'daily_guide_icon'},
            ),
            calls,
        )
        self.assertIn(('screenshot', 'daily/02_guidebook_failed'), calls)

    def test_open_daily_activity_reuses_verified_open_page(self):
        calls = []

        class Task:
            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                if args == DAILY_STAMINA_PROGRESS_BOX:
                    return []
                return [Box(14, 32, 110, 31, name='活跃行迹')]

            def wait_click_ocr(self, *args, **kwargs):
                calls.append(('wait_click_ocr', args, kwargs))
                return [Box(196, 83, 67, 31, name='活跃度')]

            def log_info(self, message):
                calls.append(('log_info', message))

            def ensure_main(self):
                raise AssertionError('must not close an already-open daily page')

        self.assertTrue(DailyTask.open_daily_activity_page(Task()))
        self.assertIn(('log_info', 'reuse the open daily activity page'), calls)

    def test_open_daily_activity_reuses_visible_stamina_row_without_navigation(self):
        calls = []
        progress_box = Box(438, 418, 70, 24, name='0/180')

        class Task:
            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                if args == DAILY_STAMINA_PROGRESS_BOX:
                    return [progress_box]
                return []

            def log_info(self, message):
                calls.append(('log_info', message))

            def ensure_main(self):
                raise AssertionError('visible /180 row must not reopen navigation')

        task = Task()
        self.assertTrue(DailyTask.open_daily_activity_page(task))
        self.assertIs(progress_box, task._daily_stamina_progress_box)
        self.assertFalse(any(call[0] == 'click_relative' for call in calls))

    def test_daily_stamina_go_uses_verified_row_and_rejects_unsafe_y(self):
        calls = []

        class Task:
            height = 1080

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

        task = Task()
        self.assertTrue(
            DailyTask.click_daily_stamina_go(
                task,
                Box(438, 418, 70, 24, name='0/180'),
            )
        )
        self.assertIn(
            (
                'click_relative',
                (DAILY_STAMINA_GO_X, 430 / 1080),
                {'name': 'daily_stamina_go', 'after_sleep': 2},
            ),
            calls,
        )

        calls.clear()
        self.assertFalse(
            DailyTask.click_daily_stamina_go(
                task,
                Box(438, 20, 70, 24, name='0/180'),
            )
        )
        self.assertFalse(any(call[0] == 'click_relative' for call in calls))

    def test_weekly_garden_is_skipped_on_macos_until_navigation_is_calibrated(self):
        calls = []

        class Task:
            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_warning(self, message):
                calls.append(('log_warning', message))

            def get_task_by_class(self, _task_class):
                raise AssertionError('legacy GardenTask coordinates must not run')

        with patch('src.task.DailyTask.sys.platform', 'darwin'):
            DailyTask.check_weekly_garden(Task())

        self.assertTrue(any(call[0] == 'log_warning' for call in calls))

    def test_standalone_garden_stops_before_legacy_macos_coordinates(self):
        calls = []

        class Task:
            def log_error(self, message):
                calls.append(('log_error', message))

            def openF2Book(self, _feature):
                raise AssertionError('legacy guidebook entry must not be clicked')

        with patch('src.task.GardenTask.sys.platform', 'darwin'):
            with self.assertRaisesRegex(Exception, 'not calibrated'):
                GardenTask.open_garden_weekly_page(Task())

        self.assertTrue(any(call[0] == 'log_error' for call in calls))

    def test_open_daily_aborts_when_activity_page_cannot_open(self):
        calls = []

        class Task:
            def open_daily_activity_page(self):
                return False

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def log_info(self, message):
                calls.append(('log_info', message))

        current, ready = DailyTask.open_daily(Task())

        self.assertIsNone(current)
        self.assertFalse(ready)
        self.assertIn(('info_set', 'current daily progress', 'unavailable'), calls)

    def test_open_daily_fails_closed_when_progress_is_unreadable(self):
        calls = []

        class Task:
            def open_daily_activity_page(self):
                return True

            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                return []

            def click(self, *args, **kwargs):
                calls.append(('click', args, kwargs))

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def get_total_daily_points(self):
                raise AssertionError('points must not be read after progress failure')

        current, ready = DailyTask.open_daily(Task())

        self.assertIsNone(current)
        self.assertFalse(ready)
        self.assertIn(
            ('log_error', 'daily stamina progress OCR failed; abort daily task'),
            calls,
        )
        self.assertNotIn(('click', ANY, ANY), calls)

    def test_open_terminal_leaves_verified_guidebook_only_once(self):
        calls = []

        class Task:
            terminal_checks = iter([False, True])

            def is_verified_terminal(self, time_out=1):
                calls.append(('is_verified_terminal', time_out))
                return next(self.terminal_checks)

            def wait_guidebook_page(self, time_out=0):
                calls.append(('wait_guidebook_page', time_out))
                return [Box(102, 52, 110, 33, name='活跃行迹')]

            def back(self, after_sleep=0):
                calls.append(('back', after_sleep))

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def ensure_main(self):
                raise AssertionError('verified guidebook must not use ensure_main')

        self.assertTrue(DailyTask.open_verified_terminal(Task()))
        self.assertEqual([('back', 1.5)], [call for call in calls if call[0] == 'back'])

    def test_open_terminal_does_not_repeat_esc_after_unknown_transition(self):
        calls = []

        class Task:
            def is_verified_terminal(self, time_out=1):
                calls.append(('is_verified_terminal', time_out))
                return False

            def wait_guidebook_page(self, time_out=0):
                calls.append(('wait_guidebook_page', time_out))
                return [Box(102, 52, 110, 33, name='活跃行迹')]

            def back(self, after_sleep=0):
                calls.append(('back', after_sleep))

            def in_team_and_world(self):
                return False

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

        self.assertFalse(DailyTask.open_verified_terminal(Task()))
        self.assertEqual([('back', 1.5)], [call for call in calls if call[0] == 'back'])

    def test_battle_pass_uses_verified_terminal_text_without_world_coordinate(self):
        calls = []

        class Task:
            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def open_verified_terminal(self):
                calls.append(('open_verified_terminal',))
                return True

            def wait_click_ocr(self, *args, **kwargs):
                calls.append(('wait_click_ocr', args, kwargs))
                if args == TERMINAL_GRID_BOX:
                    return [Box(1350, 250, 120, 50, name='先约电台')]
                if args == BATTLE_PASS_CLAIM_BOX:
                    return [Box(915, 680, 80, 32, name='键领取')]
                return None

            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                if args == BATTLE_PASS_TITLE_BOX:
                    if kwargs['match'] == BATTLE_PASS_TASK_TEXT:
                        return [Box(40, 30, 150, 50, name='电台任务')]
                    if kwargs['match'] == BATTLE_PASS_REWARD_TEXT:
                        return [Box(40, 30, 150, 50, name='先约电台')]
                    return [Box(40, 30, 150, 50, name='先约电台')]
                return []

            def ensure_main(self):
                calls.append(('ensure_main',))

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

        DailyTask.claim_battle_pass(Task())

        self.assertIn(('open_verified_terminal',), calls)
        self.assertIn(
            (
                'wait_click_ocr',
                TERMINAL_GRID_BOX,
                {
                    'match': BATTLE_PASS_ENTRY_TEXT,
                    'time_out': 3,
                    'settle_time': 0.5,
                    'after_sleep': 2,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )
        self.assertIn(
            ('click_relative', BATTLE_PASS_TASK_TAB_POSITION, {'after_sleep': 1}),
            calls,
        )
        self.assertIn(
            ('click_relative', BATTLE_PASS_REWARD_TAB_POSITION, {'after_sleep': 1}),
            calls,
        )
        self.assertNotIn(
            ('click_relative', (0.86, 0.05), {}),
            calls,
        )
        self.assertIn(
            (
                'wait_click_ocr',
                BATTLE_PASS_CLAIM_BOX,
                {
                    'match': ANY,
                    'time_out': 2,
                    'settle_time': 0.5,
                    'after_sleep': 1,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )

    def test_terminal_rewards_share_one_terminal_session(self):
        calls = []

        class Task:
            def open_verified_terminal(self):
                calls.append(('open_verified_terminal',))
                return True

            def claim_mail(self, **kwargs):
                calls.append(('claim_mail', kwargs))
                return True

            def return_to_verified_terminal(self):
                calls.append(('return_to_verified_terminal',))
                return True

            def claim_battle_pass(self, **kwargs):
                calls.append(('claim_battle_pass', kwargs))
                return True

            def sleep(self, duration):
                calls.append(('sleep', duration))

            def log_error(self, message):
                calls.append(('log_error', message))

        self.assertTrue(DailyTask.claim_terminal_rewards(Task()))
        self.assertEqual(
            [
                ('open_verified_terminal',),
                (
                    'claim_mail',
                    {'terminal_open': True, 'leave_page_open': True},
                ),
                ('return_to_verified_terminal',),
                ('sleep', 1),
                ('claim_battle_pass', {'terminal_open': True}),
            ],
            calls,
        )

    def test_mail_coordinate_is_guarded_by_terminal_and_mail_page(self):
        calls = []

        class Task:
            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def open_verified_terminal(self):
                calls.append(('open_verified_terminal',))
                return True

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

            def wait_ocr(self, *args, **kwargs):
                calls.append(('wait_ocr', args, kwargs))
                return [Box(30, 30, 80, 40, name='邮件')]

            def wait_click_ocr(self, *args, **kwargs):
                calls.append(('wait_click_ocr', args, kwargs))
                return []

            def ensure_main(self, time_out=0):
                calls.append(('ensure_main', time_out))

        claimed = DailyTask.claim_mail(Task())

        self.assertFalse(claimed)
        self.assertIn(
            ('click_relative', TERMINAL_MAIL_POSITION, {'after_sleep': 1}),
            calls,
        )
        self.assertIn(
            (
                'wait_ocr',
                MAIL_TITLE_BOX,
                {
                    'match': ANY,
                    'time_out': 3,
                    'settle_time': 0.5,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )
        self.assertIn(
            (
                'wait_click_ocr',
                MAIL_CLAIM_BOX,
                {
                    'match': ANY,
                    'time_out': 2,
                    'settle_time': 0.5,
                    'after_sleep': 1,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )

    def test_claim_daily_collects_tasks_before_guarded_milestone(self):
        calls = []

        class Task:
            claim_calls = 0

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def log_info(self, message):
                calls.append(('log_info', message))

            def open_daily_activity_page(self):
                calls.append(('open_daily_activity_page',))
                return True

            def wait_click_ocr(self, *args, **kwargs):
                calls.append(('wait_click_ocr', args, kwargs))
                if args == DAILY_TASK_CLAIM_BOX:
                    self.claim_calls += 1
                    if self.claim_calls == 1:
                        return [Box(1187, 175, 42, 27, name='领取')]
                return []

            def get_total_daily_points(self):
                calls.append(('get_total_daily_points',))
                return 100

            def click_relative(self, *args, **kwargs):
                calls.append(('click_relative', args, kwargs))

            def ensure_main(self, time_out=0):
                calls.append(('ensure_main', time_out))

        claimed = DailyTask.claim_daily(Task())

        self.assertTrue(claimed)
        self.assertLess(
            calls.index(('wait_click_ocr', DAILY_TASK_CLAIM_BOX, {
                'match': ANY,
                'time_out': 1,
                'settle_time': 0.3,
                'after_sleep': 0.5,
                'raise_if_not_found': False,
            })),
            calls.index(('get_total_daily_points',)),
        )
        self.assertIn(
            (
                'wait_click_ocr',
                DAILY_REWARD_BOX,
                {
                    'match': ANY,
                    'time_out': 2,
                    'settle_time': 0.5,
                    'after_sleep': 1,
                    'raise_if_not_found': False,
                },
            ),
            calls,
        )
        self.assertIn(
            ('click_relative', DAILY_REWARD_POSITION, {'after_sleep': 1}),
            calls,
        )

    def test_total_daily_points_uses_tight_number_box(self):
        calls = []

        class Task:
            def wait_ocr(self, *args, **kwargs):
                calls.append((args, kwargs))
                return [Box(363, 910, 28, 39, name='100')]

            def info_set(self, key, value):
                calls.append((key, value))

        points = DailyTask.get_total_daily_points(Task())

        self.assertEqual(100, points)
        self.assertEqual(DAILY_POINTS_BOX, calls[0][0])
        self.assertEqual(2, calls[0][1]['time_out'])


if __name__ == '__main__':
    unittest.main()
