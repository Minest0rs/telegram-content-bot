"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-01 00:00:00.000000

"""

from __future__ import annotations

from typing import Union
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    publish_mode = sa.Enum("auto", "preview", name="publish_mode")
    subscription_tier = sa.Enum("free", "pro", "premium", name="subscription_tier")
    source_type = sa.Enum("web", "rss", "telegram", name="source_type")
    post_status = sa.Enum(
        "draft", "pending_approval", "published", "rejected", "failed", name="post_status"
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True, index=True),
        sa.Column("username", sa.String(64)),
        sa.Column("first_name", sa.String(128)),
        sa.Column("locale", sa.String(8), nullable=False, server_default="ru"),
        sa.Column("publish_mode", publish_mode, nullable=False, server_default="preview"),
        sa.Column("custom_system_prompt", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("tier", subscription_tier, nullable=False, server_default="free"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column(
            "posts_used_this_month",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "promo_post_counter",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("username", sa.String(64)),
        sa.Column("style_summary", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "telegram_chat_id", name="uq_channel_user_chat"),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", source_type, nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.Column("label", sa.String(256)),
        sa.Column("notes", sa.Text()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel_id",
            sa.Integer(),
            sa.ForeignKey("channels.id", ondelete="SET NULL"),
        ),
        sa.Column("status", post_status, nullable=False, server_default="draft"),
        sa.Column("topic", sa.String(512)),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(1024)),
        sa.Column("image_source", sa.String(64)),
        sa.Column("has_watermark", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_promo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("telegram_message_id", sa.BigInteger()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("posts")
    op.drop_table("sources")
    op.drop_table("channels")
    op.drop_table("subscriptions")
    op.drop_table("users")

    sa.Enum(name="post_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="source_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="subscription_tier").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="publish_mode").drop(op.get_bind(), checkfirst=True)
