import logging
from telegram import Update
from telegram.ext import ContextTypes

async def ore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reports how many hours the invoking user has spent in the lab this month."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/ore - User without username attempted to use /ore command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/ore - Unauthorized /ore attempt by @{username}")
        return
    
    # Extract services from bot_data
    database = context.bot_data["database"]
    inlabClient = context.bot_data["inlabClient"]

    # Look up the user's email via Database; this project stores mappings
    team_email = await database.email_from_username(username)
    if not team_email:
        logging.warning(f"commands/ore - No team email found for @{username}")
        await update.message.reply_html("Your Telegram username is not associated with a team email.")
        return

    # Local helper to format hours (float) into a human friendly string
    def pretty_time(hours: float) -> str:
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}h {m}m"

    # Query InLab for hours and pretty-print
    try:
        ore_data = inlabClient.oreLab(team_email)
    except Exception:
        logging.exception(f"commands/ore - Failed to retrieve lab hours for @{username}")
        await update.message.reply_html("Unable to retrieve your lab hours right now.")
        return

    if not isinstance(ore_data, (int, float)):
        ore_data = 0

    ore_str = pretty_time(ore_data)

    logging.info(f"commands/ore - User @{username} has spent {ore_str} in the lab this month")

    await update.message.reply_html(
        rf"This month you've spent <b>{ore_str}</b> in the lab!"
    )
    return
