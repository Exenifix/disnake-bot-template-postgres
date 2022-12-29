import asyncio
from typing import Any, Generic, TypeVar

import disnake

T = TypeVar("T")
TIMEOUT = object()


class BaseView(disnake.ui.View):
    def __init__(self, user_id: int, *, timeout: float | None = 180.0):
        self.user_id = user_id
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.send("This button is not for you 🤭", ephemeral=True, delete_after=3)
            return False
        return True


class GenericButton(disnake.ui.Button, Generic[T]):
    def __init__(self, return_value: T, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.return_value = return_value

    async def callback(self, interaction: disnake.MessageInteraction, /):
        view: GenericView = self.view
        view.result = self.return_value
        view.inter = interaction
        view.stop()


class GenericView(BaseView, Generic[T]):
    result: T
    inter: disnake.MessageInteraction

    def __init__(self, user_id: int, buttons: list[GenericButton[T]], *, timeout: float | None = 180.0):
        super().__init__(user_id, timeout=timeout)
        for button in buttons:
            self.add_item(button)

    async def get_result(self) -> tuple[T, disnake.MessageInteraction]:
        await self.wait()
        if self.result is TIMEOUT:
            raise asyncio.TimeoutError()
        return self.result, self.inter

    async def on_timeout(self) -> None:
        self.result = TIMEOUT
        self.stop()


class ConfirmationView(GenericView):
    def __init__(self, user_id: int):
        super().__init__(
            user_id,
            [
                GenericButton(True, label="Confirm", style=disnake.ButtonStyle.green),
                GenericButton(False, label="Cancel", style=disnake.ButtonStyle.red),
            ],
        )
