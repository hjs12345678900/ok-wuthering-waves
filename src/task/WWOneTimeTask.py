from src.task.MouseResetTask import MouseResetTask


class WWOneTimeTask:

    def run(self):
        mouse_reset_task = self.executor.get_task_by_class(MouseResetTask)
        mouse_reset_task.run()
        interaction = self.executor.interaction
        if interaction.__class__.__name__ == "PostMessageInteraction":
            interaction.activate()
        self.sleep(0.5)
