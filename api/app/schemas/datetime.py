from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def _ensure_utc(v: datetime) -> datetime:
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v


TzDatetime = Annotated[datetime, AfterValidator(_ensure_utc)]
