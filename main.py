from time import sleep
from telepotpro import Bot
from pony.orm import db_session
from modules.nocodb import NocoDB
from modules import settings, utils
from modules.database import ODG, Task
from modules.api_client import EagleAPI

bot = Bot(settings.BOT_TOKEN)
nocodb = NocoDB("https://nocodb.eagletrt.it", settings.NOCODB_API_TOKEN)
eagle_api = EagleAPI("https://api.eagletrt.it", None)
tag_cache = {
    "areas": nocodb.area_tags(),
    "workgroups": nocodb.workgroup_tags(),
    "projects": nocodb.project_tags(),
    "roles": nocodb.role_tags()
}


@db_session
def reply(msg):
    msgId = msg["message_id"]
    chatId = msg["chat"]["id"]
    threadId = msg.get("message_thread_id", None)
    text = msg.get("text", "") or msg.get("caption", "")
    text = text.replace("@eagletrtbot", "").strip()

    if not text:
        return

    # Check nocodb tags
    for tag in utils.find_tags(text.lower()):
        if tag in tag_cache["areas"]:
            members = nocodb.area_members(tag.lstrip('@'))
        elif tag in tag_cache["workgroups"]:
            members = nocodb.workgroup_members(tag.lstrip('@'))
        elif tag in tag_cache["projects"]:
            members = nocodb.project_members(tag.lstrip('@'))
        elif tag in tag_cache["roles"]:
            members = nocodb.role_members(tag.lstrip('@'))
        else:
            continue

        if members:
            tag_list = ' '.join(members)
            bot.sendMessage(chatId, f"<b>{tag}</b>:\n{tag_list}",
                            reply_to_message_id=threadId, parse_mode='HTML')

    # Hello World
    if text == "/start":
        bot.sendMessage(chatId, "Hey there!", reply_to_message_id=threadId)

    # Ore Lab
    elif text == "/ore":
        username = msg["from"].get("username", "").lower()
        if not username:
            bot.sendMessage(chatId, "You don't have a Telegram username :(", reply_to_message_id=msgId)
            return

        team_email = nocodb.email_from_username(username)
        if not team_email:
            bot.sendMessage(chatId, "You are not registered in the NocoDB database.", reply_to_message_id=msgId)
            return

        ore = eagle_api.oreLab(team_email.split('@')[0])
        ore = utils.pretty_time(ore['ore'])
        bot.sendMessage(chatId, f"This month you've spent <b>{ore}</b> in the lab!",
                        reply_to_message_id=msgId, parse_mode='HTML')

    # /inlab
    elif text == "/inlab" or "@inlab" in text.lower().split():
        inlab = eagle_api.inlab()
        tags = [
            nocodb.username_from_email(email)
            for email in inlab['people']
        ]
        if inlab['count'] == 0:
            bot.sendMessage(chatId, "The lab is currently empty :(", reply_to_message_id=threadId)
        else:
            bot.sendMessage(chatId, f"<b>{inlab['count']} people in the lab:</b>\n{' '.join(tags)}",
                            reply_to_message_id=threadId, parse_mode='HTML')

    # odg show
    elif text == "/odg" or text == "/todo":
        if not (odg := ODG.get(chatId=chatId, threadId=threadId)):
            odg = ODG(chatId=chatId, threadId=threadId)
        bot.sendMessage(chatId, f"📝 <b>Todo List</b>\n\n{odg}",
                        reply_to_message_id=threadId, parse_mode='HTML')

    # odg reset
    elif text == "/odg reset" or text == "/todo reset":
        if odg := ODG.get(chatId=chatId, threadId=threadId):
            odg.reset()
        bot.setMessageReaction((chatId, msgId), [{'type': 'emoji', 'emoji': "🎉"}])

    # odg remove
    elif text.startswith("/odg remove ") or text.startswith("/todo remove "):
        if not (odg := ODG.get(chatId=chatId, threadId=threadId)):
            odg = ODG(chatId=chatId, threadId=threadId)

        try:
            task_id = int(text.split(' ', 2)[2])
        except ValueError:
            bot.sendMessage(chatId, "❌ Task ID must be a number.", reply_to_message_id=threadId)
            return

        if (1 <= task_id <= odg.tasks.count()) and odg.remove_task(task_id-1):
            bot.setMessageReaction((chatId, msgId), [{'type': 'emoji', 'emoji': "👍"}])
        else:
            bot.sendMessage(chatId, f"❌ Task #{task_id} not found.", reply_to_message_id=threadId)

    # odg add
    elif text.startswith("/odg ") or text.startswith("/todo "):
        if not (odg := ODG.get(chatId=chatId, threadId=threadId)):
            odg = ODG(chatId=chatId, threadId=threadId)

        task = Task(
            text=text.split(' ', 1)[1],
            created_by=msg['from'].get("first_name", "") + " " + msg['from'].get("last_name", ""),
            odg=odg
        )
        bot.setMessageReaction((chatId, msgId), [{'type': 'emoji', 'emoji': "✍"}])

    # tag list
    elif text == "/tags":
        bot.sendMessage(chatId, f"#️⃣ <b>Tag List</b>\n\n"
                                f"<b>Areas</b>\n"
                                f"{', '.join(tag_cache['areas'])}\n\n"
                                f"<b>Workgroups</b>\n"
                                f"{', '.join(tag_cache['workgroups'])}\n\n"
                                f"<b>Projects</b>\n"
                                f"{', '.join(tag_cache['projects'])}\n\n"
                                f"<b>Roles</b>\n"
                                f"{', '.join(tag_cache['roles'])}",
                        reply_to_message_id=threadId, parse_mode='HTML')


bot.message_loop({'chat': reply})
while True:
    sleep(60)
