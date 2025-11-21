import logging
from pony.orm import db_session
from modules.quiz import Questions, Polls
from telegram import InputMediaPhoto
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def send_scheduled_question(bot, group_id, thread_id, area_code):
    """ Fetches a random question and sends it to the specified group and thread. """

    with db_session:

        question = Questions.select(
            lambda q: area_code in (area.name for area in q.areas)
        ).random(1)[0]
        while not question.isValid():
            question = Questions.select(
                lambda q: area_code in (area.name for area in q.areas)
            ).random(1)[0]

        answers = list(question.answers)
        images = list(question.images)
    
        qtext = f"Question {question.id}-{question.quiz.quiz_id} {question.type} | {area_code}"

        options = [a.answer_text for a in answers]
        correct_indices = [i for i, a in enumerate(answers) if a.is_correct]

        if not options or not correct_indices:
            logging.warning(f"modules/scheduler - Question {question.id}-{question.quiz.quiz_id} has no answers or correct answer defined.")
            return
        
        # Send question text and any associated images
        if len(images) == 1:
            await bot.send_photo(
                chat_id=group_id,
                message_thread_id=thread_id,
                photo=f"https://img.fs-quiz.eu/{images[0].path}", caption=f"{question.text}"
            )
        elif len(images) > 1:
            media_group = [
                InputMediaPhoto(media=f"https://img.fs-quiz.eu/{img.path}")
                for img in images
            ]
            await bot.send_media_group(
                chat_id=group_id,
                message_thread_id=thread_id,
                media=media_group
            )
            await bot.send_message(
                chat_id=group_id,
                message_thread_id=thread_id,
                text=f"{question.text}"
            )
        else:
            await bot.send_message(
                chat_id=group_id,
                message_thread_id=thread_id,
                text=f"{question.text}"
            )

        logging.info(f"modules/scheduler - Scheduled question {question.id}-{question.quiz.quiz_id} | {area_code} sent to group {group_id} in thread {thread_id}.")
        
        # Send the poll with the question options
        message = await bot.send_poll(
            chat_id=group_id,
            message_thread_id=thread_id,
            question=qtext,
            options=options,
            type="quiz",
            correct_option_id=correct_indices[0],
            is_anonymous=False,
        )

        # Store the mapping between the poll ID and the question in the database
        Polls(poll_id=message.poll.id, question=question, correct_option=correct_indices[0])

    return

def setup_scheduler(application):
    """ Sets up and starts the scheduler for sending questions. """

    scheduler = AsyncIOScheduler()
    config = application.bot_data["config"]

    gen_scheduler(scheduler, application, 'Engineering', config)
    gen_scheduler(scheduler, application, 'Operations', config)

    scheduler.start()
    logging.info("modules/scheduler - Scheduler started.")

    return

def gen_scheduler(scheduler, application, division, config) -> None:
    """Generates scheduled jobs for a specific division based on configuration."""
        
    group_id = config['ScheduledQuestions'][division]["GroupID"]
    threads = config['ScheduledQuestions'][division]["Threads"]
    area = config['ScheduledQuestions'][division]["area"]
    schedulings = config['ScheduledQuestions'][division]["Scheduling"]

    for i, thread_id in enumerate(threads):
        cron_schedule = schedulings[i]
        scheduler.add_job(
            send_scheduled_question,
            'cron',
            args=[application.bot, group_id, thread_id, area[i]],
            **{field: value for field, value in zip(['minute', 'hour', 'day', 'month', 'day_of_week'], cron_schedule.split())}
        )
        logging.info(f"modules/scheduler - Job scheduled for division {division}, group {group_id}, thread {thread_id}, area {area[i]} with cron '{cron_schedule}'")

    return