import asyncio
import logging
from dataclasses import dataclass, field
from os import getenv
from typing import Any

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from tech_fields import *

import json

TOKEN = getenv("BOT_TOKEN")

@dataclass
class Question:
    text: str
    type: str
    variants: list = field(default_factory=list)
    answer: str = "-"

que_json = json.load(open("./questions/light_of_gospel.json"))
QUESTIONS = []
for que in que_json["questions"].values():
    if que["type"] == "poll":
        QUESTIONS.append(Question(text=que["text"], type=que["type"], variants=que["poll_fields"]))
    else:
        QUESTIONS.append(Question(text=que["text"], type=que["type"]))
QUESTIONS.append(Question(text="Ваш профиль в телеграмме скрытый, напишите ваш номер телефона, чтобы с вами могли связаться", type="text"))
    
# print(QUESTIONS)

class QuizScene(Scene, state="quiz"):

    @on.poll_answer.enter()
    @on.message.enter()
    async def on_enter(self, message: Message, state: FSMContext, step: int | None = 0) -> Any:
        if not step:
            await message.answer(que_json["start_text"])
        
        if step == len(QUESTIONS) - 1:
            if (hasattr(message, "from_user") and message.from_user.username is not None) or (message.user.username is not None): #type: ignore
                data = await state.get_data()
                
                answers = data.get("answers", {})
                if hasattr(message, "from_user"):
                    answers[step] = "https://t.me/" + message.from_user.username #type: ignore
                else:
                    answers[step] = "https://t.me/" + message.user.username #type: ignore
                return await self.wizard.exit()
            else:
                await self.wizard.retake(step=step+1) #type: ignore

        markup = ReplyKeyboardBuilder()
        if step > 0: # type: ignore
            markup.button(text="🔙 Назад")

        await state.update_data(step=step)
        if QUESTIONS[step].type == "poll": #type: ignore
            return await message.answer_poll(question=QUESTIONS[step].text, #type: ignore
                            options=QUESTIONS[step].variants, #type: ignore
                            is_anonymous=False, 
                            reply_markup=markup.adjust(2).as_markup(resize_keyboard=True),
        )
        try:
            return await message.answer(
                text=QUESTIONS[step].text, # type: ignore
                reply_markup=markup.adjust(2).as_markup(resize_keyboard=True),
            )
        except:
            print("boyya")

    @on.poll_answer.exit()
    async def on_exit_poll(self, poll_answer: PollAnswer, state: FSMContext) -> None:
        data = await state.get_data()
        answers = data.get("answers", {})
        questionnaire = zip([x.text for x in QUESTIONS], answers.values())
        
        text = "Спасибо, ваша заявка принята"
        # for x,y in questionnaire:
        #     text = text + f"{x}: {y}\n"
        
        users = json.load(open("./users.json"))
        users["users"].append(poll_answer.user.id) #type: ignore
        json.dump(users, open("./users.json", "w"))
        
        sheet.append_row(list(answers.values()))
        await poll_answer.bot.send_message(chat_id=poll_answer.user.id, text=text, reply_markup=ReplyKeyboardRemove()) # type: ignore
        await state.set_data({})

    @on.message.exit()
    async def on_exit(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        answers = data.get("answers", {})
        questionnaire = zip([x.text for x in QUESTIONS], answers.values())
        
        text = "Спасибо, ваша заявка принята"
        # for x,y in questionnaire:
        #     text = text + f"{x}: {y}\n"
        
        users = json.load(open("./users.json"))
        users["users"].append(message.from_user.id) #type: ignore
        json.dump(users, open("./users.json", "w"))
        
        sheet.append_row(list(answers.values()))
        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        await state.set_data({})

    @on.message(F.text == "🔙 Назад")
    async def back(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        step = data["step"]

        previous_step = step - 1
        if previous_step < 0:
            return await self.wizard.exit()
        return await self.wizard.back(step=previous_step)
        
    @on.poll_answer()
    async def poll_answer(self, poll_answer: PollAnswer, state: FSMContext) -> None:
        data = await state.get_data()
        step = data["step"]
        answers = data.get("answers", {})
        
        answer_id = poll_answer.option_ids[0]
        if QUESTIONS[step].variants[answer_id] == QUESTIONS[step].variants[-1]:
            await poll_answer.bot.send_message( #type: ignore
                chat_id=poll_answer.user.id, #type: ignore
                text="Вы выбрали 'Свой вариант'. Пожалуйста, напишите его:",)
            await state.update_data(awaiting_custom_answer_for_step=step)
        else:
            answers[step] = QUESTIONS[step].variants[answer_id]  # перезаписываем "Свой вариант" на реальный текст
            await state.update_data(answers=answers, awaiting_custom_answer_for_step=None)
            await self.wizard.retake(step=step+1)
            
    @on.message(F.text)
    async def answer(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        step = data["step"]
        
        awaiting_step = data.get("awaiting_custom_answer_for_step")
        if awaiting_step is not None:
            # Это кастомный ответ — сохраняем его вместо предыдущего
            answers = data.get("answers", {})
            answers[awaiting_step] = message.text  # перезаписываем "Свой вариант" на реальный текст
            await state.update_data(answers=answers, awaiting_custom_answer_for_step=None)
            # Теперь переходим на следующий вопрос
            await self.wizard.retake(step=awaiting_step + 1)
        
        if QUESTIONS[step].type != "poll":        
            answers = data.get("answers", {})
            answers[step] = message.text
            await state.update_data(answers=answers)

            await self.wizard.retake(step=step + 1)
        else:
            print("executed")
            pass

quiz_router = Router(name=__name__)
quiz_router.message.register(QuizScene.as_handler(), Command("start"))

def create_dispatcher():
    dispatcher = Dispatcher(events_isolation=SimpleEventIsolation())
    dispatcher.include_router(quiz_router)
    
    scene_registry = SceneRegistry(dispatcher)
    scene_registry.add(QuizScene)

    return dispatcher

async def on_startup() -> None:
    await bot.set_webhook(url=f"{BASE_URL}{WEBHOOK_PATH}",allowed_updates=["message", "chat_member"])
    
async def on_shutdown() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()


def main():
    dp = create_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    app = web.Application()
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=HOST, port=PORT)
    
    # await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()