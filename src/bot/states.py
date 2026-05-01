"""FSM states for the bot."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AddChannel(StatesGroup):
    waiting_for_channel = State()


class AddSource(StatesGroup):
    waiting_for_value = State()


class EditPrompt(StatesGroup):
    waiting_for_text = State()


class GeneratePost(StatesGroup):
    choose_channel = State()
    choose_period = State()
    enter_topic = State()
    confirm = State()
