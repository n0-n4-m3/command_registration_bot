import asyncio
import logging
from dataclasses import dataclass, field
from os import getenv
from typing import Any

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, SceneRegistry, ScenesManager, on
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import KeyboardButton, Message, ReplyKeyboardRemove, PollAnswer
from aiogram.utils.formatting import (
    Bold,
    as_key_value,
    as_list,
    as_numbered_list,
    as_section,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.handlers import PollHandler

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
    
print(QUESTIONS)

class QuizScene(Scene, state="quiz"):

    @on.message.enter()
    async def on_enter(self, message: Message, state: FSMContext, step: int | None = 0) -> Any:
        if not step:
            # This is the first step, so we should greet the user
            await message.answer("Welcome to the quiz!")

        try:
            quiz = QUESTIONS[step] # type: ignore
        except IndexError:
            # This error means that the question's list is over
            return await self.wizard.exit()

        markup = ReplyKeyboardBuilder()
        if step > 0: # type: ignore
            markup.button(text="🔙 Назад")
        markup.button(text="🚫 Выход")

        await state.update_data(step=step)
        if QUESTIONS[step].type == "poll": #type: ignore
            return await message.answer_poll(question=QUESTIONS[step].text, #type: ignore
                            options=QUESTIONS[step].variants, #type: ignore
                            is_anonymous=False, 
                            reply_markup=markup.adjust(2).as_markup(resize_keyboard=True),
        )
        return await message.answer(
            text=QUESTIONS[step].text, # type: ignore
            reply_markup=markup.adjust(2).as_markup(resize_keyboard=True),
        )

    @on.message.exit()
    async def on_exit(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        answers = data.get("answers", {})

        correct = 0
        incorrect = 0
        user_answers = []
        for step, quiz in enumerate(QUESTIONS):
            answer = answers.get(step)
            is_correct = answer == quiz.correct_answer
            if is_correct:
                correct += 1
                icon = "✅"
            else:
                incorrect += 1
                icon = "❌"
            if answer is None:
                answer = "no answer"
            user_answers.append(f"{quiz.text} ({icon} {html.quote(answer)})")

        content = as_list(
            as_section(
                Bold("Your answers:"),
                as_numbered_list(*user_answers),
            ),
            "",
            as_section(
                Bold("Summary:"),
                as_list(
                    as_key_value("Correct", correct),
                    as_key_value("Incorrect", incorrect),
                ),
            ),
        )

        await message.answer(**content.as_kwargs(), reply_markup=ReplyKeyboardRemove())
        await state.set_data({})

    @on.message(F.text == "🔙 Back")
    async def back(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        step = data["step"]

        previous_step = step - 1
        if previous_step < 0:
            # In case when the user tries to go back from the first question,
            # we just exit the quiz
            return await self.wizard.exit()
        return await self.wizard.back(step=previous_step)

    @on.message(F.text == "🚫 Exit")
    async def exit(self, message: Message) -> None:
        await self.wizard.exit()
        
    @on.poll_answer()
    async def poll_answer(self, poll_answer: PollAnswer, state: FSMContext) -> None:

        answer_id = poll_answer.option_ids[0]
        if answer_id != poll_answer.option_ids[-1]:
            data = await state.get_data()
            step = data["step"]
            answers = data.get("answers", {})
            answers[step] = QUESTIONS[step].variants[answer_id]
            await state.update_data(answer=answers)

        await self.wizard.retake(step=step + 1)

    @on.message(F.text)
    async def answer(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        step = data["step"]
        answers = data.get("answers", {})
        answers[step] = message.text
        await state.update_data(answer=answers)

        await self.wizard.retake(step=step + 1)

quiz_router = Router(name=__name__)
# Add handler that initializes the scene
quiz_router.message.register(QuizScene.as_handler(), Command("quiz"))


@quiz_router.message(Command("start"))
async def command_start(message: Message, scenes: ScenesManager):
    await scenes.close()
    await message.answer(
        "Hi! This is a quiz bot. To start the quiz, use the /quiz command.",
        reply_markup=ReplyKeyboardRemove(),
    )


def create_dispatcher():
    # Event isolation is needed to correctly handle fast user responses
    dispatcher = Dispatcher(
        events_isolation=SimpleEventIsolation(),
    )
    dispatcher.include_router(quiz_router)

    # To use scenes, you should create a SceneRegistry and register your scenes there
    scene_registry = SceneRegistry(dispatcher)
    # ... and then register a scene in the registry
    # by default, Scene will be mounted to the router that passed to the SceneRegistry,
    # but you can specify the router explicitly using the `router` argument
    scene_registry.add(QuizScene)

    return dispatcher


async def main():
    dp = create_dispatcher()
    bot = Bot(token=TOKEN) # type: ignore
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Alternatively, you can use aiogram-cli:
    # `aiogram run polling quiz_scene:create_dispatcher --log-level info --token BOT_TOKEN`
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())