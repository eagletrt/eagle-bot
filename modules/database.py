from datetime import datetime
from pony.orm import Database, Required, Optional, Set

db = Database("sqlite", "/data/eagletrtbot.db", create_db=True)


class Task(db.Entity):
    text = Required(str)
    created_by = Required(str)
    created_at = Required(datetime, default=datetime.now)
    priority = Required(int, default=0, index="priority_asc")
    odg = Required("ODG")

    def __str__(self):
        return f"📋 {self.text}\n👤 {self.created_by}"


class ODG(db.Entity):
    chatId = Required(int, sql_type='BIGINT', size=64)
    threadId = Optional(int, sql_type='BIGINT', size=64)
    tasks = Set(Task, reverse="odg")

    def __str__(self):
        if self.tasks.is_empty():
            return "Todo List empty."
        return "\n\n".join(str(task) for task in self.tasks.order_by(Task.created_at))

    def reset(self):
        for task in self.tasks:
            task.delete()
        self.tasks.clear()

    def remove_task(self, task_idx: int) -> bool:
        task = self.tasks.order_by(Task.created_at).limit(1, offset=task_idx)
        if task:
            task[0].delete()
            return True
        return False


db.generate_mapping(create_tables=True)
