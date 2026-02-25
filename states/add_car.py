from aiogram.fsm.state import State, StatesGroup
class AddCarStates(StatesGroup):
    photos = State()
    model = State()
    price = State()
    condition = State()
    transmission = State()
    color = State()
    mileage = State()
    region = State()
    confirm = State()
