import unittest

import numpy as np

from ok.feature.Box import Box
from src.Labels import Labels
from src.char.Aemeath import Aemeath
from src.char.Changli import Changli
from src.char.Mornye import Mornye
from src.task.BaseCombatTask import BaseCombatTask
from src.task.BaseWWTask import BaseWWTask, START_CHALLENGE_TEXT
from src.task.CharacterMaterialTask import (
    AUTO_MATERIAL,
    CHARACTER_MATERIAL_TYPE,
    CULTIVATION_TARGET,
    FALLBACK_STAGE_NAME,
    SAVE_COMBAT_DEBUG_FRAMES,
    CharacterMaterialTask,
    RESONATOR_EXP,
    WEAPON_AND_SKILL,
)


class TestCharacterMaterialTask(unittest.TestCase):
    def test_combat_waits_for_full_concerto_before_switching(self):
        task = CharacterMaterialTask.__new__(CharacterMaterialTask)

        self.assertTrue(task.wait_for_full_con_before_switch())
        self.assertTrue(task.use_sparse_con_ring_detection())

    def test_combat_debug_frame_queues_a_copy_in_timestamped_folder(self):
        source_frame = np.zeros((2, 3, 3), dtype=np.uint8)
        queued = []

        class Executor:
            @staticmethod
            def nullable_frame():
                return source_frame

        task = CharacterMaterialTask.__new__(CharacterMaterialTask)
        task._executor = Executor()
        task._combat_debug_frame_count = 0
        task.screenshot = lambda name, frame: queued.append((name, frame))

        self.assertTrue(task._capture_combat_debug_frame())
        self.assertEqual(
            'character_material_combat_frames/frame',
            queued[0][0],
        )
        self.assertIsNot(source_frame, queued[0][1])
        self.assertEqual(1, task._combat_debug_frame_count)

    def test_combat_debug_frame_option_name_is_stable(self):
        self.assertEqual(
            'Save Combat Frames for Debug',
            SAVE_COMBAT_DEBUG_FRAMES,
        )

    def test_material_profile_keeps_explicit_team_when_icons_are_unreadable(self):
        task = CharacterMaterialTask.__new__(CharacterMaterialTask)
        task.chars = [None, None, None]
        task._preferred_farming_team_hints = (
            Labels.char_aemeath,
            Labels.chang_changli,
            Labels.char_moning,
        )
        task.get_box_by_name = lambda name: name
        task.find_one = lambda *args, **kwargs: None
        task.log_info = lambda *args, **kwargs: None

        chars = [
            BaseCombatTask._load_char_slot(task, index, f'box_char_{index + 1}')
            for index in range(3)
        ]

        self.assertEqual([Aemeath, Changli, Mornye], [
            type(char) for char in chars
        ])

    def test_material_profile_cycles_aemeath_changli_mornye(self):
        task = CharacterMaterialTask.__new__(CharacterMaterialTask)
        task._preferred_farming_team_hints = (
            Labels.char_aemeath,
            Labels.chang_changli,
            Labels.char_moning,
        )
        chars = [
            Aemeath(task, 0),
            Changli(task, 1),
            Mornye(task, 2),
        ]
        task.chars = chars

        self.assertIs(
            chars[1],
            task._choose_switch_target(
                chars[0],
                False,
            ),
        )
        self.assertIs(
            chars[2],
            task._choose_switch_target(
                chars[1],
                False,
            ),
        )
        self.assertIs(
            chars[0],
            task._choose_switch_target(
                chars[2],
                False,
            ),
        )

    def test_aemeath_enhanced_e_is_pressed_immediately(self):
        sent = []

        class Task:
            def find_one(self, name, threshold=None, **kwargs):
                self.last_threshold = threshold
                self.last_match_options = kwargs
                return object() if name == 'aemeath_e1' else None

            def get_resonance_key(self):
                return 'e'

            def send_key(self, key, **kwargs):
                sent.append((key, kwargs))

        task = Task()
        aemeath = Aemeath(task, 0)

        self.assertTrue(aemeath.cast_enhanced_e_if_ready())
        self.assertEqual('e', sent[0][0])
        self.assertEqual(0.12, sent[0][1]['after_sleep'])
        self.assertEqual(
            Aemeath.ENHANCED_E_MATCH_THRESHOLD,
            task.last_threshold,
        )
        self.assertEqual(
            Aemeath.ENHANCED_E_HORIZONTAL_VARIANCE,
            task.last_match_options['horizontal_variance'],
        )
        self.assertEqual(
            Aemeath.ENHANCED_E_VERTICAL_VARIANCE,
            task.last_match_options['vertical_variance'],
        )

    def test_aemeath_opens_with_normal_attacks(self):
        clicks = []

        class Task:
            def check_combat(self):
                pass

            def click(self, **kwargs):
                clicks.append(kwargs)

        aemeath = Aemeath(Task(), 0)

        aemeath.opening_normal_attack_burst()

        self.assertEqual(Aemeath.OPENING_NORMAL_ATTACKS, len(clicks))
        self.assertTrue(all(
            click['after_sleep'] == Aemeath.OPENING_NORMAL_ATTACK_INTERVAL
            for click in clicks
        ))

    def test_aemeath_heavy_is_followed_by_normals_and_not_retried_immediately(self):
        actions = []

        class Task:
            combat_start = 0

            def time_elapsed_accounting_for_freeze(
                    self,
                    start,
                    intro_motion_freeze=False,
            ):
                return 10000 if start < 0 else 0

            def check_combat(self):
                pass

            def click(self, **kwargs):
                actions.append(('click', kwargs))

            def sleep(self, duration):
                actions.append(('sleep', duration))

        class TrackingAemeath(Aemeath):
            def heavy_ready_state(self):
                return 'mecha'

            def heavy_wait_highlight_down(self):
                actions.append(('heavy', {}))
                return False

            def preparing_lib2(self):
                return False

        aemeath = TrackingAemeath(Task(), 0)

        self.assertTrue(aemeath.handle_heavy())
        self.assertEqual(
            Aemeath.POST_HEAVY_NORMAL_ATTACKS,
            len([action for action in actions if action[0] == 'click']),
        )
        self.assertFalse(aemeath.handle_heavy())
        self.assertEqual(
            1,
            len([action for action in actions if action[0] == 'heavy']),
        )

    def test_changli_failed_orange_r_probe_returns_without_blocking(self):
        sent = []

        class Task:
            use_liberation = True
            in_liberation = False

            def available(self, name, check_color=True, check_cd=True):
                return False

            def has_cd(self, name, char_index=None):
                return False

            def allow_immediate_visible_liberation(self):
                return True

            def time_elapsed_accounting_for_freeze(
                    self,
                    start,
                    intro_motion_freeze=False,
            ):
                return 10000 if start < 0 else 0

            def get_liberation_key(self):
                return 'r'

            def send_key(self, key, **kwargs):
                sent.append((key, kwargs))

            def wait_until(self, condition, time_out=0, **kwargs):
                self.confirm_time = time_out
                return False

            def in_team(self):
                return True, 1, 3

        task = Task()
        changli = Changli(task, 1)
        changli.is_current_char = True

        self.assertTrue(changli.should_try_liberation())
        self.assertFalse(changli.liberation_and_heavy())
        self.assertEqual(
            'r',
            sent[0][0],
        )
        self.assertEqual(
            Changli.OPTIMISTIC_LIBERATION_CONFIRM_TIME,
            task.confirm_time,
        )
        self.assertFalse(changli.should_try_liberation())

    def test_aemeath_mecha_forte_fill_is_a_heavy_ready_state(self):
        class Task:
            def find_one(self, *args, **kwargs):
                return None

            def box_of_screen_scaled(self, *args, **kwargs):
                self.forte_box_args = (args, kwargs)
                return 'mecha-forte-box'

            def calculate_color_percentage(self, color, box):
                self.forte_color = color
                self.forte_box = box
                return 0.0923

        task = Task()
        aemeath = Aemeath(task, 0)

        self.assertEqual('mecha', aemeath.heavy_ready_state())
        self.assertEqual('mecha-forte-box', task.forte_box)
        self.assertEqual(
            Aemeath.MECHA_FORTE_READY_PERCENT,
            0.075,
        )

    def test_aemeath_human_heavy_template_precedes_mecha_probe(self):
        class Task:
            def find_one(self, name, **kwargs):
                self.match = (name, kwargs)
                return object()

            def box_of_screen_scaled(self, *args, **kwargs):
                raise AssertionError('mecha probe should not run')

        task = Task()
        aemeath = Aemeath(task, 0)

        self.assertEqual('human', aemeath.heavy_ready_state())
        self.assertEqual('aemeath_human_heavy', task.match[0])
        self.assertEqual(
            Aemeath.HUMAN_HEAVY_MATCH_THRESHOLD,
            task.match[1]['threshold'],
        )

    def test_mornye_ground_forte_heavy_precedes_normal_attack(self):
        actions = []

        class Task:
            def prefer_fast_character_rotation(self):
                return True

            def click(self, **kwargs):
                actions.append(('click', kwargs))

        class TrackingMornye(Mornye):
            stop = False

            def on_air(self):
                return self.stop

            def is_mouse_forte_full(self):
                return not self.stop

            def heavy_attack(self, duration=0.6):
                actions.append(('heavy', duration))
                self.stop = True

        mornye = TrackingMornye(Task(), 2)
        mornye.not_on_air_actions()

        self.assertEqual('click', actions[0][0])
        self.assertEqual('right', actions[0][1]['key'])
        self.assertEqual(('heavy', 0.6), actions[1])
        self.assertEqual(2, len(actions))

    def test_mouse_forte_search_covers_mornye_live_prompt_position(self):
        captured = {}
        task = BaseCombatTask.__new__(BaseCombatTask)

        def find_one(name, **kwargs):
            captured['name'] = name
            captured.update(kwargs)
            return object()

        task.find_one = find_one

        self.assertTrue(task.find_mouse_forte())
        self.assertEqual('mouse_forte', captured['name'])
        self.assertEqual(0.035, captured['horizontal_variance'])
        self.assertEqual(0.015, captured['vertical_variance'])
        self.assertEqual(0.6, captured['threshold'])

    def test_mornye_ground_liberation_precedes_resonance(self):
        actions = []

        class Task:
            @staticmethod
            def prefer_fast_character_rotation():
                return True

        class TrackingMornye(Mornye):
            stop = False

            def on_air(self):
                return self.stop

            def is_mouse_forte_full(self):
                return False

            def diagnose_mouse_forte_miss(self, context):
                pass

            def click_liberation(self, *args, **kwargs):
                actions.append('liberation')
                self.stop = True
                return True

            def cast_resonance_if_ready(self):
                actions.append('resonance')
                return True

        TrackingMornye(Task(), 2).not_on_air_actions()

        self.assertEqual(['liberation'], actions)

    def test_mornye_ready_resonance_is_sent_directly(self):
        sent = []

        class Task:
            def available(self, name, check_color=True, check_cd=True):
                self.last_available = (name, check_color, check_cd)
                return True

            def get_resonance_key(self):
                return 'e'

            def send_key(self, key, **kwargs):
                sent.append((key, kwargs))

        task = Task()
        mornye = Mornye(task, 2)
        mornye.is_current_char = True

        self.assertTrue(mornye.cast_resonance_if_ready())
        self.assertEqual(('resonance', False, True), task.last_available)
        self.assertEqual('e', sent[0][0])
        self.assertEqual(0.12, sent[0][1]['after_sleep'])

    def test_mornye_logs_failed_forte_confidence_and_saves_one_frame(self):
        screenshots = []

        class Task:
            def find_mouse_forte(self, threshold=0.6):
                self.last_probe_threshold = threshold
                return Box(1123, 987, 21, 29, 0.42, 'mouse_forte')

            def available(self, name, check_color=True, check_cd=True):
                return name == 'resonance'

            def screenshot(self, name):
                screenshots.append(name)

        task = Task()
        mornye = Mornye(task, 2)
        mornye.is_current_char = True

        mornye.diagnose_mouse_forte_miss('ground')
        mornye.diagnose_mouse_forte_miss('ground')

        self.assertEqual(
            Mornye.FORTE_DIAGNOSTIC_PROBE_THRESHOLD,
            task.last_probe_threshold,
        )
        self.assertEqual(
            ['mornye_forte_not_matched_ground_e_ready'],
            screenshots,
        )
        self.assertTrue(mornye.forte_diagnostic_screenshot_saved)

    def test_team_page_accepts_enable_challenge_wording(self):
        self.assertTrue(any(
            pattern.fullmatch('开启挑战')
            for pattern in START_CHALLENGE_TEXT
        ))

    def test_documented_character_resolves_to_forgery_category(self):
        route = CharacterMaterialTask.resolve_material_route({
            CULTIVATION_TARGET: '秧秧·玄翎',
            CHARACTER_MATERIAL_TYPE: AUTO_MATERIAL,
            FALLBACK_STAGE_NAME: '',
        })

        self.assertEqual(WEAPON_AND_SKILL, route['material_type'])
        self.assertEqual('ningsu', route['category'])
        self.assertEqual('', route['fallback_stage_name'])

    def test_unlisted_character_can_use_universal_resonator_exp(self):
        route = CharacterMaterialTask.resolve_material_route({
            CULTIVATION_TARGET: 'Another Character',
            CHARACTER_MATERIAL_TYPE: RESONATOR_EXP,
            FALLBACK_STAGE_NAME: '',
        })

        self.assertEqual('moni', route['category'])

    def test_unlisted_character_uses_avatar_marker_for_skill_material(self):
        route = CharacterMaterialTask.resolve_material_route({
            CULTIVATION_TARGET: 'Another Character',
            CHARACTER_MATERIAL_TYPE: WEAPON_AND_SKILL,
            FALLBACK_STAGE_NAME: '',
        })

        self.assertEqual('ningsu', route['category'])
        self.assertEqual('', route['fallback_stage_name'])

    def test_aemeath_material_snapshot_records_live_shortages(self):
        snapshot = CharacterMaterialTask.material_snapshot_for_target(
            '爱弥斯',
        )

        self.assertEqual('2026-07-25', snapshot['captured_at'])
        self.assertEqual(
            {
                '我们的选择': 5,
                '叠翼偏振体': 68,
                '忆中沉金': 14,
                '时苔茸': 20,
                '高频啸花声核': 2,
                '全频啸花声核': 44,
                '全频锐棱声核': 10,
            },
            {
                material['name']: material['shortage']
                for material in snapshot['materials']
            },
        )

    def test_aemeath_uses_verified_stage_when_avatar_row_is_unreadable(self):
        route = CharacterMaterialTask.resolve_material_route({
            CULTIVATION_TARGET: '爱弥斯',
            CHARACTER_MATERIAL_TYPE: AUTO_MATERIAL,
            FALLBACK_STAGE_NAME: '',
        })

        self.assertEqual('荒萋旧殿', route['fallback_stage_name'])

    def test_current_target_applies_profile_after_live_name_is_read(self):
        route = CharacterMaterialTask.resolve_material_route(
            {
                CULTIVATION_TARGET: 'Use current in-game target',
                CHARACTER_MATERIAL_TYPE: AUTO_MATERIAL,
                FALLBACK_STAGE_NAME: '',
            },
            actual_target_name='爱弥斯 预告',
        )

        self.assertEqual(WEAPON_AND_SKILL, route['material_type'])
        self.assertEqual('荒萋旧殿', route['fallback_stage_name'])

    def test_material_location_name_rejects_filter_chrome(self):
        self.assertFalse(
            BaseWWTask._valid_material_location_name('筛选武')
        )
        self.assertFalse(
            BaseWWTask._valid_material_location_name('武器培养')
        )
        self.assertTrue(
            BaseWWTask._valid_material_location_name('荒萋旧殿')
        )

    def test_false_filter_marker_does_not_override_stage_fallback(self):
        locations = [
            {
                'name': '筛选武',
                'normalized_name': '筛选武',
                'is_direct': False,
                'is_target_row': True,
                'target_marker_score': 0.80,
                'drop_fingerprint': 'f' * 64,
            },
            {
                'name': '荒萋旧殿',
                'normalized_name': '荒萋旧殿',
                'is_direct': True,
                'is_target_row': False,
                'target_marker_score': 0.01,
                'drop_fingerprint': '0' * 64,
            },
        ]

        selected = CharacterMaterialTask.equivalent_material_locations(
            locations,
            fallback_stage_name='荒萋旧殿',
        )

        self.assertEqual(['荒萋旧殿'], [
            location['name'] for location in selected
        ])

    def test_plausible_wrong_marker_does_not_override_stage_fallback(self):
        locations = [
            {
                'name': '师远熔毁废都',
                'normalized_name': '师远熔毁废都',
                'is_direct': True,
                'is_target_row': True,
                'target_marker_score': 0.80,
                'drop_fingerprint': 'f' * 64,
                'observation_count': 4,
            },
            {
                'name': '荒萋旧殿',
                'normalized_name': '荒萋旧殿',
                'is_direct': True,
                'is_target_row': False,
                'target_marker_score': 0.01,
                'drop_fingerprint': '0' * 64,
                'observation_count': 1,
            },
        ]

        selected = CharacterMaterialTask.equivalent_material_locations(
            locations,
            fallback_stage_name='荒萋旧殿',
        )

        self.assertEqual(['荒萋旧殿'], [
            location['name'] for location in selected
        ])

    def test_direct_selection_waits_for_exact_fallback_stage(self):
        wrong_direct = {
            'name': '师远熔毁废都',
            'normalized_name': '师远熔毁废都',
            'action': '直接挑战',
            'is_direct': True,
            'is_target_row': True,
            'target_marker_score': 0.80,
            'observation_count': 4,
        }

        selected = (
            CharacterMaterialTask.select_visible_direct_material_location(
                [wrong_direct],
                [wrong_direct],
                fallback_stage_name='荒萋旧殿',
            )
        )

        self.assertIsNone(selected)

    def test_unconfigured_avatar_stage_requires_repeat_observation(self):
        unstable_direct = {
            'name': 'OCR Stage',
            'normalized_name': 'ocrstage',
            'action': '直接挑战',
            'is_direct': True,
            'is_target_row': True,
            'target_marker_score': 0.80,
            'observation_count': 1,
        }

        selected = CharacterMaterialTask.equivalent_material_locations(
            [unstable_direct],
        )

        self.assertEqual([], selected)

    def test_drop_fingerprint_never_changes_to_another_material(self):
        locations = [
            {
                'name': 'Target Stage',
                'normalized_name': 'targetstage',
                'is_direct': False,
                'is_target_row': True,
                'target_marker_score': 0.30,
                'drop_fingerprint': '0' * 64,
                'material_icon_fingerprints': (
                    '0' * 64,
                    '1' * 64,
                    '2' * 64,
                ),
            },
            {
                'name': 'Equivalent Direct Stage',
                'normalized_name': 'equivalentdirectstage',
                'is_direct': True,
                'is_target_row': False,
                'target_marker_score': 0.01,
                'drop_fingerprint': '0' * 63 + '1',
                'material_icon_fingerprints': (
                    '0' * 63 + '1',
                    '1' * 63 + '0',
                    '2' * 63 + '3',
                ),
            },
            {
                'name': 'Wrong Direct Stage',
                'normalized_name': 'wrongdirectstage',
                'is_direct': True,
                'is_target_row': False,
                'target_marker_score': 0.01,
                'drop_fingerprint': 'f' * 64,
                'material_icon_fingerprints': (
                    'f' * 64,
                    'e' * 64,
                    'd' * 64,
                ),
            },
        ]

        equivalent = CharacterMaterialTask.equivalent_material_locations(
            locations,
        )
        ordered = CharacterMaterialTask.order_material_locations(equivalent)

        self.assertEqual(
            ['Equivalent Direct Stage', 'Target Stage'],
            [location['name'] for location in ordered],
        )

    def test_stage_name_is_only_a_fallback_for_missing_avatar_marker(self):
        locations = [
            {
                'name': '陨翼云渊',
                'normalized_name': '陨翼云渊',
                'is_target_row': False,
                'target_marker_score': 0.01,
                'drop_fingerprint': None,
            },
        ]

        selected = CharacterMaterialTask.equivalent_material_locations(
            locations,
            fallback_stage_name='陨翼云渊',
        )

        self.assertEqual(['陨翼云渊'], [
            location['name'] for location in selected
        ])

    def test_visible_matching_direct_challenge_is_selected_immediately(self):
        target = {
            'name': 'Target Stage',
            'normalized_name': 'targetstage',
            'is_direct': False,
            'is_target_row': True,
            'drop_fingerprint': '0' * 64,
            'material_icon_fingerprints': (
                '0' * 64,
                '1' * 64,
                '2' * 64,
            ),
        }
        matching_direct = {
            'name': 'Matching Direct Stage',
            'normalized_name': 'matchingdirectstage',
            'action': '直接挑战',
            'is_direct': True,
            'is_target_row': False,
            'drop_fingerprint': '0' * 63 + '1',
            'material_icon_fingerprints': (
                '0' * 63 + '1',
                '1' * 63 + '0',
                '2' * 63 + '3',
            ),
        }
        wrong_direct = {
            'name': 'Wrong Direct Stage',
            'normalized_name': 'wrongdirectstage',
            'action': '直接挑战',
            'is_direct': True,
            'is_target_row': False,
            'drop_fingerprint': 'f' * 64,
            'material_icon_fingerprints': (
                'f' * 64,
                'e' * 64,
                'd' * 64,
            ),
        }

        selected = (
            CharacterMaterialTask.select_visible_direct_material_location(
                [wrong_direct, matching_direct],
                [target, wrong_direct, matching_direct],
            )
        )

        self.assertIs(matching_direct, selected)

    def test_visible_direct_challenge_waits_for_verified_target_marker(self):
        unverified_direct = {
            'name': 'Unverified Direct Stage',
            'normalized_name': 'unverifieddirectstage',
            'action': '直接挑战',
            'is_direct': True,
            'is_target_row': False,
            'target_marker_score': 0.06,
            'drop_fingerprint': '0' * 64,
            'material_icon_fingerprints': ('0' * 64,),
        }

        selected = (
            CharacterMaterialTask.select_visible_direct_material_location(
                [unverified_direct],
                [unverified_direct],
            )
        )

        self.assertIsNone(selected)

    def test_character_material_enters_visible_direct_without_restore(self):
        calls = []
        target = {
            'name': 'Target Stage',
            'normalized_name': 'targetstage',
            'action': '前往',
            'is_direct': False,
            'is_target_row': True,
            'drop_fingerprint': '0' * 64,
            'material_icon_fingerprints': ('0' * 64,),
        }
        matching_direct = {
            'name': 'Matching Direct Stage',
            'normalized_name': 'matchingdirectstage',
            'action': '直接挑战',
            'is_direct': True,
            'is_target_row': False,
            'drop_fingerprint': '0' * 63 + '1',
            'material_icon_fingerprints': ('0' * 63 + '1',),
        }

        class Task:
            select_visible_direct_material_location = staticmethod(
                CharacterMaterialTask.select_visible_direct_material_location
            )

            def open_boss_book(self, category):
                calls.append(('open', category))

            def build_material_page_dictionary(
                    self,
                    category,
                    force=False,
                    visible_selector=None):
                calls.append(('build', category, force))
                selected = visible_selector(
                    [matching_direct],
                    [target, matching_direct],
                )
                return {
                    'locations': [target, matching_direct],
                    'selected_visible_location': selected,
                }

            def info_set(self, key, value):
                calls.append(('info', key, value))

            def log_info(self, message):
                calls.append(('log', message))

            def enter_visible_material_location(self, location):
                calls.append(('visible_enter', location['name']))
                return True

            def enter_material_location(self, location):
                calls.append(('restore_enter', location['name']))
                raise AssertionError('indexed row restore must not run')

        entered = CharacterMaterialTask.enter_character_material_domain(
            Task(),
            {
                'category': 'ningsu',
                'fallback_stage_name': '',
            },
        )

        self.assertTrue(entered)
        self.assertIn(
            ('visible_enter', 'Matching Direct Stage'),
            calls,
        )
        self.assertFalse(any(
            call[0] == 'restore_enter'
            for call in calls
        ))

    def test_current_target_name_excludes_labels(self):
        class Task:
            _normalize_material_text = staticmethod(
                BaseWWTask._normalize_material_text
            )

            def ocr(self, *_args, **_kwargs):
                return [
                    Box(190, 110, 100, 25, name='培养目标'),
                    Box(190, 145, 100, 25, name='秧秧·玄翎'),
                    Box(310, 110, 30, 25, name='UP'),
                ]

        self.assertEqual(
            '秧秧·玄翎',
            BaseWWTask.current_material_target_name(Task()),
        )

    def test_target_choice_accepts_name_split_across_ocr_boxes(self):
        class Task:
            _normalize_material_text = staticmethod(
                BaseWWTask._normalize_material_text
            )

            def ocr(self, *_args, **_kwargs):
                return [
                    Box(500, 300, 60, 25, name='秧秧'),
                    Box(565, 301, 80, 25, name='玄翎'),
                ]

            def width_of_screen(self, ratio):
                return 1920 * ratio

        choice = CharacterMaterialTask._visible_target_choice(
            Task(),
            '秧秧·玄翎',
        )

        self.assertIsNotNone(choice)
        self.assertEqual('玄翎', choice.name)

    def test_material_location_restore_scrolls_to_exact_direct_challenge(self):
        calls = []
        indexed = {
            'name': '荒萋旧殿',
            'normalized_name': '荒萋旧殿',
            'action': '直接挑战',
            'is_direct': True,
            'scroll_anchor': 0.64,
            'row_y': 0.47,
        }
        locked_neighbor = {
            'name': '余烬终课',
            'normalized_name': '余烬终课',
            'action': '前往',
            'is_direct': False,
            'row_y': 0.47,
        }
        restored = {
            'name': '荒萋旧殿',
            'normalized_name': '荒萋旧殿',
            'action': '直接挑战',
            'is_direct': True,
            'row_y': 0.47,
        }

        class Destination:
            name = 'team_close'

        class Task:
            visible_calls = 0

            _exact_material_location = staticmethod(
                BaseWWTask._exact_material_location
            )
            _search_material_location_by_scrolling = (
                BaseWWTask._search_material_location_by_scrolling
            )
            enter_visible_material_location = (
                BaseWWTask.enter_visible_material_location
            )

            def click(self, x, y, after_sleep):
                calls.append(('click', x, y, after_sleep))

            def _visible_material_locations(self, scroll_position):
                self.visible_calls += 1
                calls.append(('visible', scroll_position))
                if self.visible_calls < 6:
                    return [locked_neighbor]
                return [restored]

            def scroll_relative(self, x, y, count):
                calls.append(('scroll', x, y, count))

            def sleep(self, seconds):
                calls.append(('sleep', seconds))

            def log_info(self, message):
                calls.append(('info', message))

            def log_error(self, message):
                calls.append(('error', message))

            def wait_feature(self, names, **kwargs):
                calls.append(('wait_feature', names))
                return Destination()

            def finish_domain_destination(self, is_team_page):
                calls.append(('finish', is_team_page))
                return True

        entered = BaseWWTask.enter_material_location(Task(), indexed)

        self.assertTrue(entered)
        self.assertEqual(
            24,
            calls.count(('scroll', 0.88, 0.72, 2)),
        )
        self.assertEqual(
            [0.64, 0, 1, 2, 3, 4],
            [call[1] for call in calls if call[0] == 'visible'],
        )
        self.assertIn(
            ('click', 0.895, restored['row_y'], 1),
            calls,
        )
        self.assertEqual(
            1,
            calls.count(('click', 0.895, restored['row_y'], 1)),
        )
        self.assertIn(
            ('info', 'select material location 荒萋旧殿 (直接挑战)'),
            calls,
        )
        self.assertNotIn(
            ('info', 'select material location 余烬终课 (前往)'),
            calls,
        )
        self.assertIn(('finish', True), calls)
        self.assertFalse(any(
            call[0] == 'wait_feature'
            for call in calls
        ))

    def test_material_location_identity_includes_action_type(self):
        indexed = {
            'normalized_name': '荒萋旧殿',
            'is_direct': True,
        }
        locked_copy = {
            'normalized_name': '荒萋旧殿',
            'is_direct': False,
        }

        selected = BaseWWTask._exact_material_location(
            indexed,
            [locked_copy],
        )

        self.assertIsNone(selected)


if __name__ == '__main__':
    unittest.main()
