import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from ok.feature.Box import Box
from ok.feature.Feature import Feature
from ok.feature.FeatureSet import FeatureSet
from src.task.BaseWWTask import BaseWWTask


class TestFeatureSet(unittest.TestCase):
    def test_wait_in_team_with_esc_uses_guarded_ensure_main(self):
        calls = []

        class Task:
            def ensure_main(self, **kwargs):
                calls.append(('ensure_main', kwargs))
                return True

            def wait_until(self, *_args, **_kwargs):
                raise AssertionError('unguarded post_action loop must not run')

        self.assertTrue(
            BaseWWTask.wait_in_team_and_world(
                Task(),
                time_out=12,
                raise_if_not_found=True,
                esc=True,
            )
        )
        self.assertEqual(
            [('ensure_main', {'esc': True, 'time_out': 12})],
            calls,
        )

    def test_ensure_main_closes_only_one_layer_after_a_failed_probe(self):
        calls = []

        class Task:
            logged_in = True
            executor = SimpleNamespace(
                interaction=SimpleNamespace(clickable=lambda: True),
            )
            probe_results = iter([None, True])

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def wait_until(self, *_args, **_kwargs):
                return next(self.probe_results)

            def is_main(self, esc=True):
                calls.append(('is_main', esc))
                return False

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def back(self, after_sleep=0):
                calls.append(('back', after_sleep))

            def sleep(self, duration):
                calls.append(('sleep', duration))

        with patch('src.task.BaseWWTask.sys.platform', 'win32'):
            self.assertTrue(BaseWWTask.ensure_main(Task(), time_out=30))
        self.assertEqual([('back', 2)], [call for call in calls if call[0] == 'back'])
        self.assertTrue(all(call == ('is_main', False) for call in calls if call[0] == 'is_main'))

    def test_ensure_main_never_sends_esc_from_unknown_macos_page(self):
        calls = []

        class Task:
            logged_in = True
            executor = SimpleNamespace(
                interaction=SimpleNamespace(clickable=lambda: True),
            )

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def wait_until(self, *_args, **_kwargs):
                return None

            def log_info(self, message):
                calls.append(('log_info', message))

            def log_error(self, message):
                calls.append(('log_error', message))

            def back(self, after_sleep=0):
                calls.append(('back', after_sleep))

        with patch('src.task.BaseWWTask.sys.platform', 'darwin'):
            with self.assertRaisesRegex(Exception, 'game world'):
                BaseWWTask.ensure_main(Task(), time_out=0.01)

        self.assertFalse(any(call[0] == 'back' for call in calls))
        self.assertTrue(any('no Esc was sent' in call[1] for call in calls if call[0] == 'log_error'))

    def test_ensure_main_stops_when_foreground_is_lost(self):
        calls = []

        class Task:
            logged_in = True
            executor = SimpleNamespace(
                interaction=SimpleNamespace(clickable=lambda: False),
            )

            def info_set(self, key, value):
                calls.append(('info_set', key, value))

            def log_error(self, message):
                calls.append(('log_error', message))

        with self.assertRaisesRegex(Exception, 'foreground'):
            BaseWWTask.ensure_main(Task(), time_out=30)
        self.assertFalse(any(call[0] == 'back' for call in calls))

    def test_in_team_allows_platform_ui_drift(self):
        calls = []

        class Task:
            logged_in = False

            def find_one(self, name, **kwargs):
                calls.append((name, kwargs))
                if name in ('char_2_text', 'char_3_text'):
                    return Box(0, 0, 1, 1)
                return None

        task = Task()

        self.assertEqual((True, 0, 3), BaseWWTask.in_team(task))
        self.assertTrue(task.logged_in)
        self.assertEqual(
            [
                (
                    name,
                    {
                        'threshold': 0.8,
                        'horizontal_variance': 0.03,
                        'vertical_variance': 0.03,
                    },
                )
                for name in ('char_1_text', 'char_2_text', 'char_3_text')
            ],
            calls,
        )

    def test_pickup_search_box_allows_centered_ui_horizontal_drift(self):
        task = type(
            "Task",
            (),
            {
                "get_box_by_name": lambda self, _name: Box(
                    1220,
                    545,
                    20,
                    20,
                ),
            },
        )()

        search_box = BaseWWTask.f_search_box.fget(task)

        self.assertEqual((1160, 445, 140, 150), (
            search_box.x,
            search_box.y,
            search_box.width,
            search_box.height,
        ))

    def test_template_larger_than_search_area_raises(self):
        feature_set = FeatureSet(False, 'missing.json', 0.002, 0.002, default_threshold=0.8)
        feature_set.width = 33
        feature_set.height = 37
        feature_set.feature_dict['large_template'] = Feature(np.zeros((39, 32, 3), dtype=np.uint8))

        frame = np.zeros((37, 33, 3), dtype=np.uint8)
        with self.assertRaises(cv2.error):
            feature_set.find_one_feature(
                frame,
                'large_template',
                box=Box(0, 0, 33, 37, name='small_search'),
            )


if __name__ == '__main__':
    unittest.main()
