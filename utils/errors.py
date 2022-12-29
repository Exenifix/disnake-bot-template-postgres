import inspect
import sys

from disnake import Forbidden, NotFound
from disnake.ext import commands


class _Unknown:
    pass


UNKNOWN = _Unknown()


class CustomException:
    pass


known_exceptions = [
    i[1]
    for i in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and issubclass(x, CustomException))
]

known_exceptions.extend(
    [
        commands.MissingRequiredArgument,
        commands.ArgumentParsingError,
        commands.BadArgument,
        commands.CheckFailure,
        commands.CommandNotFound,
        commands.DisabledCommand,
        commands.CommandOnCooldown,
        commands.NotOwner,
        commands.MemberNotFound,
        commands.UserNotFound,
        commands.ChannelNotFound,
        commands.RoleNotFound,
        commands.MissingPermissions,
        commands.BotMissingPermissions,
        commands.MissingRole,
        commands.MissingAnyRole,
        NotFound,
        Forbidden,
    ]
)


def get_error_msg(error: commands.CommandError):
    error = getattr(error, "original", error)
    if type(error) not in known_exceptions:
        return UNKNOWN

    return str(error)
