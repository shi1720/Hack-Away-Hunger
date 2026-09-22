"""Strict API inputs. Unknown fields and nonfinite or imprecise weights are rejected."""

import math
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

Category = Literal["produce", "protein", "dairy", "grains", "pantry"]
Storage = Literal["ambient", "chilled", "frozen"]


def weight(value: float) -> float:
    if not math.isfinite(value) or Decimal(str(value)) % Decimal("0.01"):
        raise ValueError("Weight must be finite with at most two decimal places")
    return value


Weight = Annotated[float, Field(ge=0, le=1_000_000), AfterValidator(weight)]
PositiveWeight = Annotated[float, Field(gt=0, le=1_000_000), AfterValidator(weight)]
ShortText = Annotated[str, Field(min_length=1, max_length=120)]
Notes = Annotated[str, Field(max_length=2000)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Credentials(Input):
    email: Annotated[str, Field(min_length=3, max_length=254)]
    password: Annotated[
        str, StringConstraints(strip_whitespace=False), Field(min_length=1, max_length=256)
    ]

    @field_validator("email")
    @classmethod
    def email_normalize(cls, value: str) -> str:
        import re

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value.lower()


class Registration(Credentials):
    name: ShortText
    network_name: ShortText
    password: Annotated[
        str, StringConstraints(strip_whitespace=False), Field(min_length=12, max_length=256)
    ]


class Join(Credentials):
    name: ShortText
    token: Annotated[str, Field(min_length=20, max_length=200)]
    password: Annotated[
        str, StringConstraints(strip_whitespace=False), Field(min_length=12, max_length=256)
    ]


class Invite(Input):
    role: Literal["coordinator", "driver"]


class SiteInput(Input):
    name: ShortText
    city: ShortText
    address: Annotated[str, Field(min_length=1, max_length=300)]
    lat: Annotated[float, Field(ge=-90, le=90)]
    lng: Annotated[float, Field(ge=-180, le=180)]
    storage_types: Annotated[list[Storage], Field(min_length=1, max_length=3)]
    capacity_lb: PositiveWeight
    notes: Notes = ""

    @field_validator("storage_types")
    @classmethod
    def unique_storage(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Storage types must be unique")
        return value


class SiteUpdate(Input):
    name: ShortText | None = None
    city: ShortText | None = None
    address: Annotated[str, Field(min_length=1, max_length=300)] | None = None
    lat: Annotated[float, Field(ge=-90, le=90)] | None = None
    lng: Annotated[float, Field(ge=-180, le=180)] | None = None
    storage_types: Annotated[list[Storage], Field(min_length=1, max_length=3)] | None = None
    capacity_lb: PositiveWeight | None = None
    notes: Notes | None = None


class DatedInput(Input):
    @field_validator("expires_at", "service_at", check_fields=False)
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        if value is None:
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must include a timezone")
        return value.astimezone(UTC)


class LotInput(DatedInput):
    site_id: ShortText
    food_name: ShortText
    category: Category
    storage: Storage
    quantity_lb: PositiveWeight
    reserve_lb: Weight = 0
    expires_at: datetime
    restricted: bool = False
    notes: Notes = ""


class LotUpdate(DatedInput):
    version: Annotated[int, Field(ge=1)]
    site_id: ShortText | None = None
    food_name: ShortText | None = None
    category: Category | None = None
    storage: Storage | None = None
    quantity_lb: Weight | None = None
    reserve_lb: Weight | None = None
    expires_at: datetime | None = None
    restricted: bool | None = None
    notes: Notes | None = None


class NeedInput(DatedInput):
    site_id: ShortText
    category: Category
    quantity_lb: PositiveWeight
    service_at: datetime
    notes: Notes = ""


class PlanInput(Input):
    max_distance_miles: Annotated[float, Field(gt=0, le=500)] = 50
    vehicle_capacity_lb: PositiveWeight = 500
    refrigerated: bool = True


class TransferInput(PlanInput):
    lot_id: ShortText
    need_id: ShortText
    quantity_lb: PositiveWeight


class AcceptInput(Input):
    receiver_name: ShortText


class PickupInput(Input):
    temperature_f: Annotated[float, Field(ge=-100, le=180)] | None = None
    condition_confirmed: Literal[True]


class ReceiveInput(Input):
    received_lb: Weight
    temperature_f: Annotated[float, Field(ge=-100, le=180)] | None = None
    receiver_name: ShortText
    exception_reason: Notes = ""


class CancelInput(Input):
    reason: Annotated[str, Field(min_length=3, max_length=2000)]
