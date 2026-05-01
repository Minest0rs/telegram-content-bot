"""All aiogram routers."""

from aiogram import Router

from src.bot.handlers import (
    channels,
    common,
    generate,
    payments,
    sources,
    style,
    subscription,
)


def get_root_router() -> Router:
    router = Router(name="root")
    router.include_router(common.router)
    router.include_router(channels.router)
    router.include_router(sources.router)
    router.include_router(style.router)
    router.include_router(subscription.router)
    router.include_router(payments.router)
    router.include_router(generate.router)
    return router


__all__ = ["get_root_router"]
