import logging
from telegram import Update
from telegram.ext import ContextTypes

async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Generates a shlink QR code and sends it to the user. """

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/qr - User without username attempted to use /qr command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if username not in context.bot_data['config']['Whitelist']['QRcode']:
        logging.warning(f"commands/qr - Unauthorized /qr attempt by @{username}")
        return

    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    shlink = context.bot_data["shlink_api"]

    # Parse arguments: first is URL, second (optional) is custom code
    url = text.split(' ')[1] if text.count(' ') >= 1 else None
    code = text.split(' ')[2] if text.count(' ') >= 2 else None

    if not url:
        logging.warning(f"commands/qr - User @{username} did not provide a URL for QR code generation")
        await update.message.reply_text("Please provide a URL to generate a QR code. Usage: /qr <URL> [custom-code]")
        return
    
    try:
        # Generate short URL and QR code
        short_url = shlink.generate_short_url(url, code)
        qr_image = shlink.generate_qr_code(short_url)

        logging.info(f"commands/qr - Successfully generated QR code for user @{username} with URL: {short_url}")
        await update.message.reply_photo(qr_image, caption=f"Here is your short URL: {short_url}")
    except Exception as e:
        logging.error(f"commands/qr - Error generating QR code for user @{username}: {e}")
        await update.message.reply_text("An error occurred while generating the QR code. Please try again later.")
    return