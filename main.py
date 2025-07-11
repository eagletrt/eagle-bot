from time import sleep
from telepotpro import Bot
from modules.nocodb import NocoDB
from modules import settings, utils
from modules.api_client import EagleAPI

bot = Bot(settings.BOT_TOKEN)
nocodb = NocoDB("https://nocodb.eagletrt.it", settings.NOCODB_API_TOKEN)
eagleApi = EagleAPI("https://api.eagletrt.it", "")
tag_cache = {
    "areas": nocodb.area_tags(),
    "workgroups": nocodb.workgroup_tags(),
    "projects": nocodb.project_tags(),
    "roles": nocodb.role_tags()
}


def reply(msg):
    msgId = msg["message_id"]
    chatId = msg["chat"]["id"]
    userId = msg["from"]["id"]
    theadId = msg.get("message_thread_id", msgId)
    text = msg.get("text", "").replace("@eagletrtbot", "").strip()

    if chatId not in settings.CHAT_WHITELIST and not settings.DEBUG_MODE:
        bot.sendMessage(chatId, f"This bot is not available in this chat.\nid: <code>{chatId}</code>",
                        reply_to_message_id=theadId, parse_mode='HTML')
        return

    # Check area tags
    for tag in tag_cache["areas"]:
        if tag.lower() in text.lower().split():
            members = nocodb.area_members(tag.strip('@'))
            tag_list = ' '.join(members)
            bot.sendMessage(chatId, f"<b>{tag}</b>:\n{tag_list}",
                            reply_to_message_id=theadId, parse_mode='HTML')

    # Check workgroup tags
    for tag in tag_cache["workgroups"]:
        if tag.lower() in text.lower().split():
            members = nocodb.workgroup_members(tag.strip('@'))
            tag_list = ' '.join(members)
            bot.sendMessage(chatId, f"<b>{tag}</b>:\n{tag_list}",
                            reply_to_message_id=theadId, parse_mode='HTML')

    # Check project tags
    for tag in tag_cache["projects"]:
        if tag.lower() in text.lower().split():
            members = nocodb.project_members(tag.strip('@'))
            tag_list = ' '.join(members)
            bot.sendMessage(chatId, f"<b>{tag}</b>:\n{tag_list}",
                            reply_to_message_id=theadId, parse_mode='HTML')

    # Check role tags
    for tag in tag_cache["roles"]:
        if tag.lower() in text.lower().split():
            members = nocodb.role_members(tag.strip('@'))
            tag_list = ' '.join(members)
            bot.sendMessage(chatId, f"<b>{tag}</b>:\n{tag_list}",
                            reply_to_message_id=theadId, parse_mode='HTML')

    # Ore Lab
    if text == "/ore":
        username = msg["from"].get("username", "")
        if not username:
            bot.sendMessage(chatId, "You don't have a Telegram username :(", reply_to_message_id=msgId)
            return

        team_user = nocodb.email_from_username(username).split('@')[0]
        if not team_user:
            bot.sendMessage(chatId, "You are not registered in the NocoDB database.", reply_to_message_id=msgId)
            return

        ore = eagleApi.oreLab(team_user)
        ore = utils.pretty_time(ore['ore'])
        bot.sendMessage(chatId, f"This month you've spent <b>{ore}</b> in the lab!",
                        reply_to_message_id=msgId, parse_mode='HTML')

    # /inlab
    elif text == "/inlab" or "@inlab" in text.lower().split():
        inlab = eagleApi.inlab()
        tags = [
            nocodb.username_from_email(email)
            for email in inlab['people']
        ]
        if inlab['count'] == 0:
            bot.sendMessage(chatId, "The lab is currently empty :(", reply_to_message_id=msgId)
        else:
            bot.sendMessage(chatId, f"<b>{inlab['count']} people in the lab:</b>\n{' '.join(tags)}",
                            reply_to_message_id=msgId, parse_mode='HTML')


bot.message_loop({'chat': reply})
while True:
    sleep(60)
