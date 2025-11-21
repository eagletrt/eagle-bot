import logging
from pony.orm import db_session
from modules.quiz import Questions
from telegram import Update
from telegram.ext import ContextTypes
import re

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the correct answer(s) for a given question ID."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/answer - User without username attempted to use /answer command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['Quiz']):
        logging.warning(f"commands/answer - Unauthorized /answer attempt by @{username}")
        return
    
    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    # Extract question ID from the command text
    id = text.split(' ', 1)[1] if ' ' in text else None

    if not id or not re.fullmatch(r"\d+-\d+", id):
        logging.info(f"commands/answer - Invalid question ID format from @{username}: {id}")
        await update.message.reply_html("Invalid question ID format. Use &lt;question_id&gt;-&lt;quiz_id&gt;.")
        return
    
    id_parts = id.split('-', 1)
    question_id = id_parts[0]
    quiz_id = id_parts[1]

    # Fetch the question and its answers from the database
    with db_session:
        question_entity = Questions.get(id=question_id, quiz=quiz_id)
        if not question_entity:
            logging.info(f"commands/answer - Question with ID {id} not found for user @{username}")
            await update.message.reply_html(f"Question with ID {id} not found.")
            return
        answers = list(question_entity.answers)
    
    # Format the answers, indicating which are correct
    answer_texts = []
    for ans in answers:
        indicator = "✅" if ans.is_correct else "❌"
        answer_texts.append(f"{indicator} {ans.answer_text}")

    logging.info(f"commands/answer - User @{username} requested correctly answers for question {question_id} in quiz {quiz_id} areas ({question_entity.areas})")

    await update.message.reply_html(
        f"<b>Answers for Question ID {question_id} in Quiz ID {quiz_id}:</b>\n" + "\n".join(answer_texts)
    )
    return
