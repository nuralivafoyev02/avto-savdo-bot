from aiogram.fsm.state import State, StatesGroup
class SearchCarStates(StatesGroup):
    waiting_for_model = State()
    waiting_for_price_min = State()
    waiting_for_price_max = State()
