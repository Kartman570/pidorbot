import random
import re
from telegram import ForceReply, Update, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from data import offenses, answers
import json
import os
from dotenv import load_dotenv

users = {}


def save_user(chat_id, user):
    load_users()
    chat_id = str(chat_id)
    if chat_id not in users:
        users[chat_id] = []
    if user not in users[chat_id]:
        users[chat_id].append(user)
        with open("./users.json", 'w') as f:
            json.dump(users, f)
        print(f"Added user - {user} to chat {chat_id}\nActual list of users: {users}")


def load_users():
    global users
    try:
        if os.path.exists("./users.json") and os.path.getsize("./users.json") > 0:
            with open("./users.json", 'r') as f:
                users = json.load(f)
                users = {str(k): v for k, v in users.items()}
        else:
            users = {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading users: {e}")
        users = {}


def get_random_user(chat_id: str, except_user: str = False):
    global users
    if chat_id in users:
        userlist = users[chat_id]
        if except_user:
            userlist.remove(except_user)
        return random.choice(userlist)
    print(f"ERROR chat {chat_id} not found")
    return None


def random_chance(chance):
    return random.randint(1, 100) <= chance


class DialogEngine(object):
    @staticmethod
    def choose_answer(message, sender):
        text = message.text
        chat_id = str(message.chat_id)

        for question, config in answers.items():
            if re.search(question, text):
                if random_chance(config['chance']):
                    answer = random.choice(config['responses'])
                    if "%%%RANDOMUSER%%%" in answer:
                        random_user = get_random_user(chat_id, sender)
                        if random_user:
                            answer = answer.replace("%%%RANDOMUSER%%%", "@" + random_user)
                    if "%%%SENDER%%%" in answer:
                        answer = answer.replace("%%%SENDER%%%", "@" + sender)

                    return answer

        if random_chance(1):
            answer = random.choice(offenses)
            if "%%%RANDOMUSER%%%" in answer:
                random_user = get_random_user(chat_id, sender)
                if random_user:
                    answer = answer.replace("%%%RANDOMUSER%%%", "@" + random_user)
            if "%%%SENDER%%%" in answer:
                answer = answer.replace("%%%SENDER%%%", "@" + sender)
            return answer
        return None


dialog_engine = DialogEngine()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.username
    chat_id = str(update.effective_chat.id)
    print(f"id: {user_id}, chat_id: {chat_id}, message: {update.message.text}")

    save_user(chat_id, user_id)
    reply = dialog_engine.choose_answer(update.message, update.effective_user.username)
    if reply:
        await update.message.reply_text(reply)


def main() -> None:
    load_users()
    print(f"Actual list of users: {users}")

    load_dotenv(".env")
    TOKEN = os.environ.get("TOKEN")
    application = Application.builder().token(TOKEN).build()

    # application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
