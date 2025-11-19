import logging
from telegram import Update
from telegram.ext import ContextTypes
from pony.orm import db_session
from modules.quiz import Polls

async def question_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Handles answers to quiz questions. """
    
    answer = update.poll_answer
    poll_id = answer.poll_id
    user = answer.user

    # Retrieve the options from your stored poll data
    with db_session:
        options = Polls.get(poll_id=poll_id)
        if options is None:
            logging.warning(f"commands/question - Received answer for unknown poll ID {poll_id} from user @{user.username}")
            return
        options = {
            "question_id": options.question.id,
            "quiz_id": options.question.quiz.quiz_id,
            "correct_option": options.correct_option,
            "areas": options.question.areas
        }

    # Check if the user retracted their vote
    if not answer.option_ids:
        # This is where you log the vote retraction
        logging.info(f"commands/question - User @{user.username} retracted their vote for poll ID {poll_id}")
        return
    
    selected_option = answer.option_ids[0]
    correct_option = options['correct_option']
    
    nocodb = context.bot_data['nocodb']
    if selected_option == correct_option:
        logging.info(f"commands/question - User @{user.username} answered correctly for question {options['question_id']}-{options['quiz_id']} | ({options['areas']})")
        await nocodb.quiz_answer_log(user.username, True)
    else:
        logging.info(f"commands/question - User @{user.username} answered incorrectly for question {options['question_id']}-{options['quiz_id']} | ({options['areas']})")
        await nocodb.quiz_answer_log(user.username, False)

    return