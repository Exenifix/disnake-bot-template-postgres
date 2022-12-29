from dotenv import load_dotenv
from exenenv import EnvironmentProfile, EnvVar, UnloadedVariables


class MainEnvironment(EnvironmentProfile):
    TOKEN: str


class DatabaseEnvironment(EnvironmentProfile):
    DSN: str | None = EnvVar(default=None, converter=str)
    DATABASE: str
    USER: str
    PASSWORD: str | None = EnvVar(default=None, converter=str)
    HOST: str = "127.0.0.1"
    PORT: int = 5432


load_dotenv()

main = MainEnvironment()
main.load()

db = DatabaseEnvironment()
try:
    db.load()
except UnloadedVariables as exc:
    if db.DSN is None:
        raise exc from None
