import re
import sys

from qfluentwidgets import FluentIcon

from ok import Logger, TaskDisabledException
from src.task.BaseWWTask import GUIDEBOOK_MENU_POSITION, number_re
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
from src.task.FarmEchoTask import FarmEchoTask
from src.task.ForgeryTask import ForgeryTask
from src.task.GardenTask import GardenTask
from src.task.MergeEchoTask import MergeEchoTask
from src.task.NightmareNestTask import NightmareNestTask
from src.task.TacetTask import TacetTask
from src.task.SimulationTask import SimulationTask
from src.task.WWOneTimeTask import WWOneTimeTask
from src.task.BaseCombatTask import BaseCombatTask

logger = Logger.get_logger(__name__)

CHECK_WEEKLY_GARDEN = 'Check Weekly Garden'
AUTO_FARM_NIGHTMARE_NEST = 'Auto Farm all Nightmare Nest'
MERGE_ECHO_IF_DISCARDED_OVER_1000 = 'Merge Echo If discarded > 1000'
TELEPORT_AND_FARM_4C_ECHO = 'Teleport and Farm 4C Echo'
ADDITIONAL_TASKS = 'Additional Tasks to Run After Daily Task'
DAILY_GUIDE_POSITION = (0.038, 0.173)
DAILY_PAGE_TITLE_BOX = (0.00, 0.00, 0.18, 0.10)
DAILY_STAMINA_PROGRESS_BOX = (0.18, 0.15, 0.48, 0.82)
DAILY_STAMINA_GO_X = 0.885
DAILY_POINTS_BOX = (0.16, 0.82, 0.25, 0.90)
DAILY_ACTIVITY_TAB_BOX = (0.05, 0.04, 0.35, 0.20)
DAILY_TASK_CLAIM_BOX = (0.80, 0.16, 0.98, 0.79)
DAILY_REWARD_BOX = (0.75, 0.72, 0.99, 0.98)
DAILY_REWARD_POSITION = (0.930, 0.893)
TERMINAL_TITLE_BOX = (0.00, 0.00, 0.23, 0.16)
TERMINAL_GRID_BOX = (0.42, 0.10, 0.96, 0.88)
TERMINAL_MAIL_POSITION = (0.653, 0.955)
MAIL_TITLE_BOX = (0.00, 0.00, 0.25, 0.18)
MAIL_CLAIM_BOX = (0.02, 0.72, 0.34, 0.98)
BATTLE_PASS_TITLE_BOX = (0.00, 0.00, 0.20, 0.10)
BATTLE_PASS_TASK_TAB_POSITION = (0.038, 0.303)
BATTLE_PASS_REWARD_TAB_POSITION = (0.038, 0.177)
BATTLE_PASS_CLAIM_BOX = (0.55, 0.84, 0.79, 0.96)

DAILY_ACTIVITY_TEXT = [
    re.compile(r'^活跃度$'),
    re.compile(r'^活躍度$'),
    re.compile(r'^Activity$', re.IGNORECASE),
]
DAILY_PAGE_TITLE_TEXT = [
    re.compile(r'^活跃行迹$'),
    re.compile(r'^活躍行跡$'),
    re.compile(r'^Activity Milestones?$', re.IGNORECASE),
]
TERMINAL_TITLE_TEXT = [
    re.compile(r'^终端$'),
    re.compile(r'^終端$'),
    re.compile(r'^Terminal$', re.IGNORECASE),
]
MAIL_TITLE_TEXT = [
    re.compile(r'^邮件$'),
    re.compile(r'^郵件$'),
    re.compile(r'^Mail$', re.IGNORECASE),
]
BATTLE_PASS_ENTRY_TEXT = [
    re.compile(r'^先约电台$'),
    re.compile(r'^先約電台$'),
    re.compile(r'^Pioneer Podcast$', re.IGNORECASE),
]
BATTLE_PASS_TASK_TEXT = [
    re.compile(r'^电台任务$'),
    re.compile(r'^電台任務$'),
    re.compile(r'^Podcast Quests?$', re.IGNORECASE),
]
BATTLE_PASS_REWARD_TEXT = [
    *BATTLE_PASS_ENTRY_TEXT,
    re.compile(r'^电台奖励$'),
    re.compile(r'^電台獎勵$'),
    re.compile(r'^电台等级$'),
    re.compile(r'^電台等級$'),
    re.compile(r'^(Podcast )?Rewards?$', re.IGNORECASE),
]
CLAIM_TEXT = [
    re.compile(r'^一键领取$'),
    re.compile(r'^一鍵領取$'),
    re.compile(r'^键领取$'),
    re.compile(r'^鍵領取$'),
    re.compile(r'^全部领取$'),
    re.compile(r'^全部領取$'),
    re.compile(r'^领取$'),
    re.compile(r'^領取$'),
    re.compile(r'^Claim All$', re.IGNORECASE),
    re.compile(r'^Claim$', re.IGNORECASE),
]


class DailyTask(WWOneTimeTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Daily Task"
        self.group_name = "Daily"
        self.group_icon = FluentIcon.CALENDAR
        self.icon = FluentIcon.CAR
        self.support_schedule_task = True
        self.support_tasks = [
            'Character Materials',
            'Tacet Suppression',
            'Forgery Challenge',
            'Simulation Challenge',
        ]
        self.default_config = {
            'Which to Farm': self.support_tasks[0],
            CULTIVATION_TARGET: '秧秧·玄翎',
            CHARACTER_MATERIAL_TYPE: AUTO_MATERIAL,
            FALLBACK_STAGE_NAME: '',
            SAVE_COMBAT_DEBUG_FRAMES: False,
            'Which Tacet Suppression to Farm': 1,  # starts with 1
            'Which Forgery Challenge to Farm': 1,  # starts with 1
            'Material Selection': 'Shell Credit',
            'Farm Nightmare Nest for Daily Echo': True,
            ADDITIONAL_TASKS: [CHECK_WEEKLY_GARDEN],
        }
        self.config_description = {
            CULTIVATION_TARGET: (
                'Exact character name shown under Cultivation Target on the '
                'Material Acquisition page.'
            ),
            CHARACTER_MATERIAL_TYPE: (
                'Choose which material for the selected character should '
                'consume the daily waveplates.'
            ),
            FALLBACK_STAGE_NAME: (
                'Optional stage name used only if the target-avatar marker '
                'cannot be detected. It is not a material name.'
            ),
            SAVE_COMBAT_DEBUG_FRAMES: (
                'Save material-domain combat frames at 5 Hz for debugging.'
            ),
            'Which Tacet Suppression to Farm': 'The Tacet Suppression number in the F2 list.',
            'Which Forgery Challenge to Farm': 'The Forgery Challenge number in the F2 list.',
            'Material Selection': 'Resonator EXP / Weapon EXP / Shell Credit',
            'Farm Nightmare Nest for Daily Echo': 'Farm 1 Echo from Nightmare Nest to complete Daily Task when needed.',
            ADDITIONAL_TASKS: 'Select optional tasks. Nightmare Nest runs before stamina farming to help complete '
                              'the daily task; the other tasks run afterward.',
        }
        material_option_list = ['Resonator EXP', 'Weapon EXP', 'Shell Credit']
        self.config_type = {
            'Which to Farm': {
                'type': "drop_down",
                'options': self.support_tasks,
                'sub_configs': {
                    'Character Materials': [
                        CULTIVATION_TARGET,
                        CHARACTER_MATERIAL_TYPE,
                        FALLBACK_STAGE_NAME,
                        SAVE_COMBAT_DEBUG_FRAMES,
                    ],
                    'Tacet Suppression': ['Which Tacet Suppression to Farm'],
                    'Forgery Challenge': ['Which Forgery Challenge to Farm'],
                    'Simulation Challenge': [
                        'Material Selection'],
                }
            },
            CHARACTER_MATERIAL_TYPE: {
                'type': 'drop_down',
                'options': [AUTO_MATERIAL, RESONATOR_EXP, WEAPON_AND_SKILL],
            },
            'Material Selection': {
                'type': 'drop_down',
                'options': material_option_list
            },
            ADDITIONAL_TASKS: {
                'type': 'multi_selection',
                'options': [
                    CHECK_WEEKLY_GARDEN,
                    AUTO_FARM_NIGHTMARE_NEST,
                    MERGE_ECHO_IF_DISCARDED_OVER_1000,
                    TELEPORT_AND_FARM_4C_ECHO,
                ],
            },
        }
        self.add_exit_after_config()
        self.description = "Login, claim monthly card, farm echo, and claim daily reward"

    def run(self):
        if not self.validate_additional_tasks():
            return

        WWOneTimeTask.run(self)
        self.logged_in = False

        additional_tasks = self.config.get(ADDITIONAL_TASKS) or []
        condition1 = AUTO_FARM_NIGHTMARE_NEST in additional_tasks
        condition2 = self.config.get('Farm Nightmare Nest for Daily Echo')

        used_stamina, daily_reward_ready = self.open_daily()
        if used_stamina is None:
            self.log_error('daily page could not be opened; abort the remaining daily task')
            return
        need_stamina = not daily_reward_ready and used_stamina < 180
        need_nightmare = condition1 or (
                condition2
                and not daily_reward_ready
                and self.config.get('Which to Farm', self.support_tasks[0]) != 'Tacet Suppression'
        )

        if need_nightmare:
            try:
                # 劫持 NightmareNestTask.ensure_main 避免梦魇打完关书
                self.get_task_by_class(NightmareNestTask).ensure_main = lambda *args, **kwargs: None

                if condition1:
                    self.log_debug('Auto Farm all Nightmare Nest')
                    self.run_task_by_class(NightmareNestTask)
                elif condition2:
                    self.log_debug('Farm Nightmare Nest for Daily Echo')
                    self.get_task_by_class(NightmareNestTask).run_capture_mode()
            except TaskDisabledException:
                raise
            except Exception as e:
                self.log_error("NightmareNestTask Failed", e)
                self.screenshot('NightmareNestTask')
                self.ensure_main(time_out=180)
            finally:
                # 还原 ensure_main，防范实例状态污染
                self.get_task_by_class(NightmareNestTask).__dict__.pop('ensure_main', None)

        if need_stamina:
            target = self.config.get('Which to Farm', self.support_tasks[0])
            if target == 'Character Materials':
                self.get_task_by_class(CharacterMaterialTask).farm_character_materials(
                    daily=True,
                    used_stamina=used_stamina,
                    config=self.config,
                )
            elif target == 'Tacet Suppression':
                self.get_task_by_class(TacetTask).farm_tacet(daily=True, used_stamina=used_stamina,
                                                             config=self.config)
            elif target == 'Forgery Challenge':
                self.get_task_by_class(ForgeryTask).farm_forgery(daily=True, used_stamina=used_stamina,
                                                                 config=self.config)
            elif target == 'Simulation Challenge':
                self.get_task_by_class(SimulationTask).farm_simulation(daily=True, used_stamina=used_stamina,
                                                                       config=self.config)
            else:
                raise ValueError(f'Unknown daily farming target: {target}')
            self.sleep(4)

        self.claim_daily()

        self.claim_terminal_rewards()
        self.run_additional_tasks()
        self.log_info('Daily Task Completed', notify=True)

    def validate_additional_tasks(self):
        additional_tasks = self.config.get(ADDITIONAL_TASKS) or []
        if TELEPORT_AND_FARM_4C_ECHO in additional_tasks:
            farm_echo_task = self.get_task_by_class(FarmEchoTask)
            if farm_echo_task.config.get('Teleport to Boss', 'No') == 'No':
                self.log_error(
                    self.tr(
                        'Teleport and Farm 4C Echo requires "Teleport to Boss" to be enabled in Farm Echo Task.'
                    ),
                    notify=True,
                )
                return False
        if AUTO_FARM_NIGHTMARE_NEST in additional_tasks:
            nightmare_task = self.get_task_by_class(NightmareNestTask)
            if not nightmare_task.config.get('Which to Farm'):
                self.log_error(
                    self.tr(
                        'Auto Farm all Nightmare Nest requires at least one "Which to Farm" option.'
                    ),
                    notify=True,
                )
                return False
        return True

    def run_additional_tasks(self):
        additional_tasks = self.config.get(ADDITIONAL_TASKS) or []
        if CHECK_WEEKLY_GARDEN in additional_tasks:
            self.check_weekly_garden()
        if MERGE_ECHO_IF_DISCARDED_OVER_1000 in additional_tasks:
            self.check_discarded_echo()
        if TELEPORT_AND_FARM_4C_ECHO in additional_tasks:
            self.log_info('Daily task completed, start teleport to farm 4C echo', notify=True)
            self.run_task_by_class(FarmEchoTask)

    def check_weekly_garden(self):
        self.info_set('current task', 'check weekly garden')
        self.log_info('check weekly garden')
        if sys.platform == 'darwin':
            # The current guidebook's second entry is Wandering Journal, while
            # GardenTask still follows the former second-entry layout. Do not
            # let its legacy coordinates run against an unrelated page.
            self.log_warning(
                'weekly garden navigation is not calibrated for the current '
                'macOS guidebook; skip it safely'
            )
            return
        try:
            garden_task = self.get_task_by_class(GardenTask)
            garden_task.open_garden_weekly_page()
            if garden_task.is_weekly_garden_completed():
                self.log_info('weekly garden already completed')
                return
            self.log_info('weekly garden not completed, run GardenTask')
            self.run_task_by_class(GardenTask)
        except TaskDisabledException:
            raise
        except Exception as e:
            self.log_error("GardenTask Failed", e)
            self.screenshot('GardenTask')
            self.ensure_main(time_out=180)

    def check_discarded_echo(self):
        self.info_set('current task', 'check discarded echo')
        self.log_info('check discarded echo')
        merge_echo_task = self.get_task_by_class(MergeEchoTask)
        old_notify_if_not_enough = merge_echo_task.notify_if_not_enough
        try:
            merge_echo_task.notify_if_not_enough = False
            self.run_task_by_class(MergeEchoTask)
        except TaskDisabledException:
            raise
        except Exception as e:
            self.log_error("MergeEchoTask Failed", e)
            self.screenshot('MergeEchoTask')
            self.ensure_main(time_out=180)
        finally:
            merge_echo_task.notify_if_not_enough = old_notify_if_not_enough

    def claim_terminal_rewards(self):
        """Claim mail and battle-pass rewards in one terminal session."""
        if not self.open_verified_terminal():
            self.log_error('terminal could not be opened; skip terminal rewards')
            return False

        self.claim_mail(terminal_open=True, leave_page_open=True)
        if not self.return_to_verified_terminal():
            self.log_error('could not return from mail to terminal; skip battle pass')
            return False

        self.sleep(1)
        return self.claim_battle_pass(terminal_open=True)

    def claim_battle_pass(self, terminal_open=False):
        self.log_info('battle pass')
        if terminal_open:
            terminal_open = self.is_verified_terminal()
        elif not self.open_verified_terminal():
            return False
        else:
            terminal_open = True
        if not terminal_open:
            self.log_error('terminal page verification failed; skip battle pass')
            return False

        entry = self.wait_click_ocr(
            *TERMINAL_GRID_BOX,
            match=BATTLE_PASS_ENTRY_TEXT,
            time_out=3,
            settle_time=0.5,
            after_sleep=2,
            raise_if_not_found=False,
        )
        if not entry or not self.wait_ocr(
            *BATTLE_PASS_TITLE_BOX,
            match=BATTLE_PASS_TASK_TEXT + BATTLE_PASS_REWARD_TEXT,
            time_out=3,
            settle_time=0.5,
            raise_if_not_found=False,
        ):
            self.log_error('battle pass page verification failed; skip claim')
            self.ensure_main()
            return False

        claimed = False
        for tab_position, page_text in (
            (BATTLE_PASS_TASK_TAB_POSITION, BATTLE_PASS_TASK_TEXT),
            (BATTLE_PASS_REWARD_TAB_POSITION, BATTLE_PASS_REWARD_TEXT),
        ):
            self.click_relative(*tab_position, after_sleep=1)
            page = self.wait_ocr(
                *BATTLE_PASS_TITLE_BOX,
                match=page_text,
                time_out=2,
                settle_time=0.5,
                raise_if_not_found=False,
            )
            if not page:
                self.log_error('battle pass tab verification failed; skip claim')
                continue
            claim = self.wait_click_ocr(
                *BATTLE_PASS_CLAIM_BOX,
                match=CLAIM_TEXT,
                time_out=2,
                settle_time=0.5,
                after_sleep=1,
                raise_if_not_found=False,
            )
            claimed = bool(claim) or claimed

        if not claimed:
            self.log_info('no verified battle pass reward to claim')
        return claimed

    def is_verified_terminal(self, time_out=1):
        return bool(self.wait_ocr(
            *TERMINAL_TITLE_BOX,
            match=TERMINAL_TITLE_TEXT,
            time_out=time_out,
            settle_time=0.3,
            raise_if_not_found=False,
        ))

    def open_verified_terminal(self):
        if self.is_verified_terminal(time_out=0.8):
            return True

        if self.wait_guidebook_page(time_out=0.8):
            self.log_info('leave the verified guidebook once to reach Terminal')
            self.back(after_sleep=1.5)
            if self.is_verified_terminal(time_out=2):
                return True
            if not self.in_team_and_world():
                self.log_error(
                    'leaving the verified guidebook reached an unknown page; '
                    'do not send another Esc'
                )
                return False
        else:
            self.ensure_main()

        # At this point the world has been positively verified.
        self.back(after_sleep=1.5)
        if self.is_verified_terminal(time_out=3):
            return True
        self.log_error('terminal page verification failed; skip guarded action')
        return False

    def return_to_verified_terminal(self, max_back_attempts=2):
        """Leave mail/popups without reopening Terminal from the world."""
        for attempt in range(max_back_attempts + 1):
            if self.is_verified_terminal():
                return True
            if self.in_team_and_world():
                self.log_error('returned to the world before terminal was verified')
                return False
            if attempt < max_back_attempts:
                self.back(after_sleep=1)
        self.log_error('terminal verification failed after leaving mail')
        return False

    def open_daily_activity_page(self):
        progress = DailyTask.wait_daily_stamina_progress(self, time_out=0.8)
        if progress:
            self._daily_stamina_progress_box = progress[0]
            self.log_info(
                f'daily activity row already visible at {progress[0].name}; '
                'skip sidebar and tab clicks'
            )
            return True

        # Reuse the already-open activity page. open_daily() leaves this page
        # active, so claim_daily() must not close and reopen it.
        page_title = self.wait_ocr(
            *DAILY_PAGE_TITLE_BOX,
            match=DAILY_PAGE_TITLE_TEXT,
            time_out=0.8,
            settle_time=0,
            raise_if_not_found=False,
        )
        if page_title:
            activity_tab = self.wait_click_ocr(
                *DAILY_ACTIVITY_TAB_BOX,
                match=DAILY_ACTIVITY_TEXT,
                time_out=2,
                settle_time=0.3,
                after_sleep=1,
                raise_if_not_found=False,
            )
            if activity_tab:
                self.log_info('reuse the open daily activity page')
                return True

        self.ensure_main()
        self.screenshot('daily/01_before_guidebook')
        book_key = self.key_config.get('Guidebook Key', self.key_config.get('索拉指南', 'f2'))
        if sys.platform == 'darwin':
            if self.in_team_and_world():
                self.log_info(f'open the guidebook with the configured {book_key} hotkey on macOS')
                self.send_key(book_key, after_sleep=4)
            if self.in_team_and_world():
                self.log_info(
                    'hotkey missed; use one atomic Alt+click on the calibrated '
                    'guidebook world icon'
                )
                self.send_key_down('alt')
                self.sleep(0.05)
                self.click_relative(*GUIDEBOOK_MENU_POSITION, name='guidebook_world_icon')
                self.sleep(0.02)
                self.send_key_up('alt')
                self.sleep(4)
            self.screenshot('daily/02_after_guidebook')
        elif self.in_team_and_world():
            self.log_info(f'click {book_key} to open the book')
            self.send_key(book_key, after_sleep=4)
        if sys.platform != 'darwin' and self.in_team_and_world():
            self.log_info('send f2 key mouse key to open the book')
            self.send_key_down('alt')
            self.sleep(0.05)
            self.click_relative(*GUIDEBOOK_MENU_POSITION, name='guidebook_world_icon')
            self.sleep(0.02)
            self.send_key_up('alt')
            self.sleep(4)
            self.screenshot('daily/02_after_guidebook')

        progress = DailyTask.wait_daily_stamina_progress(self, time_out=1)
        if progress:
            self._daily_stamina_progress_box = progress[0]
            self.log_info(
                f'found daily stamina row {progress[0].name}; '
                'skip the already-selected activity navigation'
            )
            return True

        # Never click a sidebar coordinate until a guidebook page title is
        # visible. The legacy gray_book_quest icon produces false positives in
        # the open world on the current UI.
        if not self.wait_guidebook_page(time_out=3):
            self.log_error('guidebook verification failed; skip daily page coordinate')
            self.screenshot('daily/02_guidebook_failed')
            return False

        # The former gray_book_quest template now matches the third
        # Material Acquisition icon. Use the calibrated first icon instead.
        self.click_relative(*DAILY_GUIDE_POSITION, after_sleep=1, name='daily_guide_icon')
        self.screenshot('daily/03_after_activity_icon')
        progress = DailyTask.wait_daily_stamina_progress(self, time_out=1)
        if progress:
            self._daily_stamina_progress_box = progress[0]
            return True

        page_title = self.wait_ocr(
            *DAILY_PAGE_TITLE_BOX,
            match=DAILY_PAGE_TITLE_TEXT,
            time_out=3,
            settle_time=0.5,
            raise_if_not_found=False,
        )
        if not page_title:
            self.log_error('daily page title verification failed; skip coordinate actions')
            self.screenshot('daily/04_page_title_failed')
            return False

        activity_tab = self.wait_click_ocr(
            *DAILY_ACTIVITY_TAB_BOX,
            match=DAILY_ACTIVITY_TEXT,
            time_out=3,
            settle_time=0.5,
            after_sleep=1,
            raise_if_not_found=False,
        )
        if activity_tab:
            return True
        self.log_error('daily activity page verification failed; skip coordinate actions')
        self.screenshot('daily/05_activity_tab_failed')
        return False

    def wait_daily_stamina_progress(self, time_out=1):
        return self.wait_ocr(
            *DAILY_STAMINA_PROGRESS_BOX,
            match=re.compile(r'^(\d+)/180$'),
            time_out=time_out,
            settle_time=0.2,
            raise_if_not_found=False,
        )

    def click_daily_stamina_go(self, progress_box):
        """Click the Go button on the same row as the verified /180 progress."""
        row_y = progress_box.center()[1] / self.height
        if not 0.2 <= row_y <= 0.8:
            self.log_error(
                f'daily stamina row is outside the guarded area: y={row_y:.3f}'
            )
            return False
        self.log_info(
            f'click Go on the verified {progress_box.name} row at y={row_y:.3f}'
        )
        self.click_relative(
            DAILY_STAMINA_GO_X,
            row_y,
            name='daily_stamina_go',
            after_sleep=2,
        )
        return True

    def open_daily(self):
        self.log_info('open_daily')
        if not self.open_daily_activity_page():
            # Fail closed and abort the whole task. Continuing would reopen
            # unrelated menus and hide the captured failure state.
            self.info_set('current daily progress', 'unavailable')
            self.info_set('total daily points', 0)
            return None, False

        progress_box = getattr(self, '_daily_stamina_progress_box', None)
        if hasattr(self, '_daily_stamina_progress_box'):
            del self._daily_stamina_progress_box
        if progress_box is None:
            progress = DailyTask.wait_daily_stamina_progress(self, time_out=3)
            progress_box = progress[0] if progress else None
        if progress_box:
            current = int(progress_box.name.split('/')[0])
        else:
            self.log_error('daily stamina progress OCR failed; abort daily task')
            self.info_set('current daily progress', 'unavailable')
            self.info_set('total daily points', 0)
            return None, False
        self.info_set('current daily progress', current)
        total_points = self.get_total_daily_points()
        reward_ready = total_points >= 100
        if sys.platform == 'darwin' and current < 180 and not reward_ready:
            DailyTask.click_daily_stamina_go(self, progress_box)
        return current, reward_ready
        # 请注意：如果任务【累计消耗180点结晶波片】已完成，current 也可能为 0，因为翻页后也有可能识别不到已用体力。

    def get_total_daily_points(self):
        points_boxes = self.wait_ocr(
            *DAILY_POINTS_BOX,
            match=number_re,
            time_out=2,
            settle_time=0.5,
        )
        if points_boxes:
            try:
                points = int(re.sub(r'\D', '', points_boxes[0].name))
            except Exception:
                points = 0
        else:
            points = 0
        self.info_set('total daily points', points)
        return points

    def claim_daily(self):
        self.info_set('current task', 'claim daily')
        if not self.open_daily_activity_page():
            return False

        claimed_tasks = False
        for _ in range(10):
            claim_task = self.wait_click_ocr(
                *DAILY_TASK_CLAIM_BOX,
                match=CLAIM_TEXT,
                time_out=1,
                settle_time=0.3,
                after_sleep=0.5,
                raise_if_not_found=False,
            )
            if not claim_task:
                break
            claimed_tasks = True

        points = self.get_total_daily_points()
        if points < 100:
            self.log_info('daily reward is not ready')
            return claimed_tasks

        claim = self.wait_click_ocr(
            *DAILY_REWARD_BOX,
            match=CLAIM_TEXT,
            time_out=2,
            settle_time=0.5,
            after_sleep=1,
            raise_if_not_found=False,
        )
        if not claim:
            # This coordinate is only allowed after the page title and
            # 100-point total have both been verified.
            self.log_info('claim daily reward via guarded coordinate')
            self.click_relative(*DAILY_REWARD_POSITION, after_sleep=1)
        return True

    def claim_mail(self, terminal_open=False, leave_page_open=False):
        self.info_set('current task', 'claim mail')
        if terminal_open:
            terminal_open = self.is_verified_terminal()
        elif not self.open_verified_terminal():
            return False
        else:
            terminal_open = True
        if not terminal_open:
            self.log_error('terminal page verification failed; skip mail')
            return False

        self.click_relative(*TERMINAL_MAIL_POSITION, after_sleep=1)
        if not self.wait_ocr(
            *MAIL_TITLE_BOX,
            match=MAIL_TITLE_TEXT,
            time_out=3,
            settle_time=0.5,
            raise_if_not_found=False,
        ):
            self.log_error('mail page verification failed; skip claim')
            if not leave_page_open:
                self.ensure_main(time_out=10)
            return False

        claim = self.wait_click_ocr(
            *MAIL_CLAIM_BOX,
            match=CLAIM_TEXT,
            time_out=2,
            settle_time=0.5,
            after_sleep=1,
            raise_if_not_found=False,
        )
        if not claim:
            self.log_info('no verified mail reward to claim')
        if not leave_page_open:
            self.ensure_main(time_out=10)
        return bool(claim)


from ok import run_task
from config import config

if __name__ == "__main__":
    run_task(config, task=DailyTask, debug=True)
