import logging
from modules.quiz import get_question, get_random_question, is_question_valid, get_question_answers, get_question_images, get_question_areas, create_poll
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
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/question - Unauthorized /question attempt by @{username}")
        return
    
    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    # Extract question ID from the command text
    val = text.split(' ')[1] if ' ' in text else None

    if val:
        if re.fullmatch(r"\d+-\d+", val):
            # If the parameter looks like an ID, use it (numeric-numeric).
            id = val                
            id_parts = id.split('-', 1)
            question_id = id_parts[0]
            quiz_id = id_parts[1]

            q = get_question(question_id, quiz_id)
            if not q or not is_question_valid(q['id'], q['quiz_id']):
                logging.info(f"commands/question - No valid question found for question ID {question_id} in quiz ID {quiz_id} for user @{username}")
                await update.message.reply_text(f"No valid question found for question ID {question_id} in quiz ID {quiz_id}.")
                return

        elif re.fullmatch(r"[A-Za-z]+", val):
            # If the parameter looks like an area, fetch a random question from that area.
            area_code = val.upper()

            if area_code not in context.bot_data['areas']:
                logging.info(f"commands/question - Invalid area parameter from @{username}: {area_code}")
                await update.message.reply_text("Please provide a valid question ID in the format <question_id>-<quiz_id> or a valid area name.")
                return

            q = get_random_question(area_code)
            while q and not is_question_valid(q['id'], q['quiz_id']):
                q = get_random_question(area_code)

        else:
            logging.info(f"commands/question - Invalid parameter from @{username}: {val}")
            await update.message.reply_text("Please provide a valid question ID in the format <question_id>-<quiz_id> or a valid area name.")
            return

    else:
        # If no ID, fetch a random valid question.
        q = get_random_question()
        while q and not is_question_valid(q['id'], q['quiz_id']):
            q = get_random_question()

    answers = get_question_answers(q['id'], q['quiz_id'])
    images = get_question_images(q['id'], q['quiz_id'])
    areas = get_question_areas(q['id'], q['quiz_id'])

    qtext = f"Question {q['id']}-{q['quiz_id']} {q['type']}"

    options = [a['answer_text'] for a in answers]
    correct_indices = [i for i, a in enumerate(answers) if a['is_correct']]

    if not options or not correct_indices:
        logging.warning(f"commands/question - Question {q['id']}-{q['quiz_id']} | ({areas}) has no answers or correct answer defined for user @{username}")
        await update.message.reply_text(f"No valid question found for question ID {q['id']} in quiz ID {q['quiz_id']}.")
        return
    
    # Send question text and any associated images
    if len(images) == 1:
        await update.message.reply_photo(f"https://img.fs-quiz.eu/{images[0]['path']}", caption=f"{q['text']}")
    elif len(images) > 1:
        media_group = [
            InputMediaPhoto(media=f"https://img.fs-quiz.eu/{img['path']}")
            for img in images
        ]
        await update.message.reply_media_group(media=media_group)
        await update.message.reply_text(f"{q['text']}")
    else:
        await update.message.reply_text(f"{q['text']}")

    logging.info(f"commands/question - User @{username} requested question {q['id']}-{q['quiz_id']} | ({areas}) correctly")
    
    # Send the poll with the question options
    message = await update.message.reply_poll(
        qtext,
        options,
        type="quiz",
        correct_option_id=correct_indices[0],
        is_anonymous=True,
    )

    # Store the mapping between the poll ID and the question in the database
    create_poll(message.poll.id, q['id'], q['quiz_id'], correct_indices[0])

    return
