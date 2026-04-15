from aiogram.fsm.state import StatesGroup, State

class RegEditor(StatesGroup):
    waiting_name = State()
    waiting_skills = State()
    waiting_price = State()
    waiting_skill_level = State()
    waiting_portfolio = State()
    waiting_experience = State()

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

class CreateOrder(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_budget = State()
    waiting_revision_price = State()
    waiting_deadline_mode = State()
    waiting_deadline = State()

class DealChange(StatesGroup):
    waiting_text = State()

class EditOrder(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_budget = State()
    waiting_revision_price = State()
    waiting_deadline = State()

class EditorProposal(StatesGroup):
    waiting_price = State()
    waiting_comment = State()

class ChatRequest(StatesGroup):
    waiting_text = State()

class RevisionRequest(StatesGroup):
    waiting_description = State()
    waiting_price = State()

class RevisionCounter(StatesGroup):
    waiting_price = State()

class BalanceWithdraw(StatesGroup):
    waiting_amount = State()
    waiting_description = State()

class DealChat(StatesGroup):
    chatting = State()
    waiting_link = State()

class DisputeChat(StatesGroup):
    chatting = State()

class DisputeOpenReason(StatesGroup):
    waiting_text = State()

class VerifyChat(StatesGroup):
    chatting = State()

class ModerationSearch(StatesGroup):
    waiting_query = State()

class ModerationUserLookup(StatesGroup):
    waiting_user_id = State()

class ModerationMessage(StatesGroup):
    waiting_text = State()

class ModerationRefund(StatesGroup):
    waiting_amount = State()
