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

    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

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
    
    team_email = 'filippo.pesavento@eagletrt.it' # --- FOR TESTING ONLY, IGNORE ---
    
    if text.lower().startswith("/ore week"):
        try:
            ore_data = inlabClient.oreLabWeek(team_email)
        except Exception:
            logging.exception(f"commands/ore - Failed to retrieve weekly lab hours for @{username}")
            await update.message.reply_html("Unable to retrieve your weekly lab hours right now.")
            return
        
        if not isinstance(ore_data, dict):
            logging.warning(f"commands/ore - Invalid ore data format for @{username} weekly: {ore_data}")
            ore_data = {}

        response_lines = ["This week you've spent:"]
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            hours = ore_data.get(day, 0)
            if hours > 0:
                response_lines.append(f"<b>{day}:</b> {pretty_time(hours)}")
        response = "\n".join(response_lines)

        if len(response_lines) == 1:
            response = "You haven't spent any time in the lab this week."

        logging.info(f"commands/ore - Weekly lab hours for @{username}: {response}")
        await update.message.reply_html(response)

    elif text.lower().startswith("/ore month"):
        try:
            ore_data = inlabClient.oreLabMonth(team_email)
        except Exception:
            logging.exception(f"commands/ore - Failed to retrieve monthly lab hours for @{username}")
            await update.message.reply_html("Unable to retrieve your monthly lab hours right now.")
            return

        if not isinstance(ore_data, dict):
            logging.warning(f"commands/ore - Invalid ore data format for @{username} monthly: {ore_data}")
            ore_data = {}

        response_lines = ["This month you've spent:"]
        for day in range(1, 32):
            hours = ore_data.get(day, 0)
            if hours > 0:
                response_lines.append(f"<b>{day}:</b> {pretty_time(hours)}")
        response = "\n".join(response_lines)

        if len(response_lines) == 1:
            response = "You haven't spent any time in the lab this month."

        logging.info(f"commands/ore - Monthly lab hours for @{username}: {response}")
        await update.message.reply_html(response)

    elif text.lower().startswith("/ore year"):
        #..
        return
    elif text.lower().startswith("/ore season"):
        #..
        return
    elif text.lower().startswith("/ore total"):
        #..
        return
    else:
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
