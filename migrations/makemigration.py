import uuid
from datetime import datetime, timezone

id = uuid.uuid4().hex
open(fname := f"{int(datetime.now(tz=timezone.utc).timestamp())}-{id}.sql", "w").close()
print(f"Successfully created new migration: migrations/{fname}")
