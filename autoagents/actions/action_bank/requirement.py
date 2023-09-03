from autoagents.actions import Action


class Requirement(Action):
    """Requirement without any implementation details"""
    async def run(self, *args, **kwargs):
        raise NotImplementedError
