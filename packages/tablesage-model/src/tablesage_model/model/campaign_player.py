from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel

GAME_MASTER_ROLE = "game-master"
"""Magic ``default_role_name`` value marking a roster member as the campaign's GM.

Application and TUI code must reference this constant rather than the raw
string; it is never something the user types directly (see the GM/Character
role picker in the TUI screens doc).
"""


class CampaignPlayer(SQLModel, table=True):
    """Links a player to a campaign and carries the campaign-specific default role.

    ``default_role_name`` seeds a session's role when the session is created;
    the magic value ``GAME_MASTER_ROLE`` marks this member as the campaign's GM,
    any other value is their default character name.
    """

    __tablename__ = "campaign_player"
    __table_args__ = (
        UniqueConstraint("campaign_id", "player_id", name="uq_campaign_player_campaign_id_player_id"),
        CheckConstraint("trim(default_role_name) != ''", name="ck_campaign_player_default_role_name_non_blank"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    campaign_id: uuid.UUID = Field(foreign_key="campaign.id", ondelete="CASCADE")
    player_id: uuid.UUID = Field(foreign_key="player.id", ondelete="CASCADE")
    default_role_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validates("default_role_name")
    def validate_default_role_name(self, key: str, value: str) -> str:
        if not value.strip():
            raise ValueError("default_role_name must not be blank")
        return value
