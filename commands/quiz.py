import logging
from pony.orm import db_session
from modules.quiz import Quiz
from telegram import Update
from telegram.ext import ContextTypes

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays details for a specific quiz."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/quiz - User without username attempted to use /quiz command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if username not in context.bot_data['config']['Whitelist']['QuizDB']:
        logging.warning(f"commands/quiz - Unauthorized /quiz attempt by @{username}")
        return
    
    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    # Extract quiz ID from the command text
    id = text.split(' ', 1)[1] if ' ' in text else None
    if not id:
        logging.info(f"commands/quiz - No quiz ID provided by @{username}")
        await update.message.reply_html("Please specify a quiz ID. Usage: /quiz &lt;id&gt;")
        return
    
    # Fetch the quiz from the database and reply with its details
    with db_session:
        quiz_entity = Quiz.get(quiz_id=id)
        if not quiz_entity:
            logging.info(f"commands/quiz - Quiz with ID {id} not found for user @{username}")
            await update.message.reply_html(f"Quiz with ID {id} not found.")
            return
    
    logging.info(f"commands/quiz - User @{username} requested correctly details for quiz ID {quiz_entity.quiz_id}")
    await update.message.reply_html(
        f"<b>Quiz ID {quiz_entity.quiz_id}</b>\n"
        f"Year: {quiz_entity.year}\n"
        f"Class: {quiz_entity.class_}\n"
        f"Date: {quiz_entity.date}\n"
        f"Information: {quiz_entity.information}\n"
    )
    return
