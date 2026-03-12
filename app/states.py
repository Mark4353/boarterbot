from aiogram.fsm.state import StatesGroup, State

class RegEditor(StatesGroup):
    waiting_name = State()
    waiting_skills = State()
    waiting_price = State()
    waiting_portfolio = State()

class RegClient(StatesGroup):
    waiting_name = State()

class Verify(StatesGroup):
    waiting_submission = State()

class EditEditor(StatesGroup):
    waiting_name = State()
    waiting_skills = State()
    waiting_price = State()
    waiting_portfolio = State()

class EditClient(StatesGroup):
    waiting_name = State()