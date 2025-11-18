import logging
from pony.orm import db_session
from modules.quiz import Quiz
from telegram import Update
from telegram.ext import ContextTypes

async def quizzes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all available quizzes in the database."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/quizzes - User without username attempted to use /quizzes command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['Quiz']):
        logging.warning(f"commands/qr - Unauthorized /qr attempt by @{username}")
        return
    
    # Fetch all quizzes and format them into a list for the reply
    with db_session:
        all_quizzes = Quiz.select().order_by(Quiz.quiz_id)
        if not all_quizzes:
            logging.error(f"commands/quizzes - No quizzes found for user @{username}")
            await update.message.reply_html("No quizzes found in the database.")
            return
    
        quiz_texts = []
        for q in all_quizzes:
            quiz_texts.append(f"<code>/quiz {q.quiz_id}</code> - {q.year} {q.class_}")
    
    logging.info(f"commands/quizzes - User @{username} requested correctly the list of available quizzes")
    await update.message.reply_html(
        f"<b>Available Quizzes:</b>\n" + "\n".join(quiz_texts)
    )
    return
