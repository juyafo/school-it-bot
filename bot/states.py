from aiogram.fsm.state import State, StatesGroup


class Register(StatesGroup):
    full_name = State()
    grade = State()
    days = State()
    free_time = State()
    phone = State()