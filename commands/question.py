import logging
from pony.orm import db_session
from modules.quiz import Questions, Polls
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
import re

async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a quiz question as a poll."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/question - User without username attempted to use /question command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    # Extract question ID from the command text
    id = text.split(' ', 1)[1] if ' ' in text else None

    with db_session:
        if not id:
            # If no ID, fetch a random valid question.
            # The loop ensures that a question with answers and images is selected.
            question = Questions.select().random(1)[0]
            while not question.isValid():
                question = Questions.select().random(1)[0]
        else:
            # If an ID is provided, parse it and fetch the specific question.
            if not id or not re.fullmatch(r"\d+-\d+", id):
                logging.info(f"commands/question - Invalid question ID format from @{username}: {id}")
                await update.message.reply_text("Please provide a valid question ID in the format <question_id>-<quiz_id>.")
                return
            
            id_parts = id.split('-', 1)
            question_id = id_parts[0]
            quiz_id = id_parts[1]

            question = Questions.get(id=question_id, quiz=quiz_id)
            if not question or not question.isValid():
                logging.info(f"commands/question - No valid question found for question ID {question_id} in quiz ID {quiz_id} for user @{username}")
                await update.message.reply_text(f"No valid question found for question ID {question_id} in quiz ID {quiz_id}.")
                return

        answers = list(question.answers)
        images = list(question.images)
    
        qtext = f"Question {question.id}-{question.quiz.quiz_id} {question.type}"

        options = [a.answer_text for a in answers]
        correct_indices = [i for i, a in enumerate(answers) if a.is_correct]

        if not options or not correct_indices:
            logging.warning(f"commands/question - Question {question.id}-{question.quiz.quiz_id} | ({question.areas}) has no answers or correct answer defined for user @{username}")
            await update.message.reply_text(f"No valid question found for question ID {question.id} in quiz ID {question.quiz.quiz_id}.")
            return
        
        # Send question text and any associated images
        if len(images) == 1:
            await update.message.reply_photo(f"https://img.fs-quiz.eu/{images[0].path}", caption=f"{question.text}")
        elif len(images) > 1:
            media_group = [
                InputMediaPhoto(media=f"https://img.fs-quiz.eu/{img.path}")
                for img in images
            ]
            await update.message.reply_media_group(media=media_group)
            await update.message.reply_text(f"{question.text}")
        else:
            await update.message.reply_text(f"{question.text}")

        logging.info(f"commands/question - User @{username} requested question {question.id}-{question.quiz.quiz_id} | ({question.areas}) correctly")
        
        # Send the poll with the question options
        message = await update.message.reply_poll(
            qtext,
            options,
            type="quiz",
            correct_option_id=correct_indices[0],
            is_anonymous=False,
        )

        # Store the mapping between the poll ID and the question in the database
        Polls(poll_id=message.poll.id, question=question, correct_option=correct_indices[0])

    return
