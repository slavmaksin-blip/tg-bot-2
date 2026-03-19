from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from keyboards import help_keyboard

router = Router()


@router.callback_query(F.data == "help")
async def help_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption=(
                "ℹ️ Помощь\n\n"
                "Если у вас есть вопросы, свяжитесь с поддержкой:"
            ),
            reply_markup=help_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "ℹ️ Помощь\n\nЕсли у вас есть вопросы, свяжитесь с поддержкой:",
            reply_markup=help_keyboard()
        )
    await callback.answer()
