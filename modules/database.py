# Database module for storing tasks and ODG (one-day/one-discussion-group) records
# Uses Pony ORM to map Python classes to a SQLite database

from datetime import datetime  # used for timestamps on Task creation
from pony.orm import Database, Required, Optional, Set  # Pony ORM constructs

# Create a Database object connected to a SQLite file.
# The path "/data/eagletrtbot.db" is the file location and create_db=True ensures the file is created if missing.
db = Database()
db.bind(provider="sqlite", filename="../data/eagletrtbot.db", create_db=True)

class Task(db.Entity):
    # A Task entity/table with columns defined below.
    # 'Required' means the field is non-nullable in the DB; default values are applied when appropriate.
    text = Required(str)  # The task text/content
    created_by = Required(str)  # Username or identifier of the creator
    created_at = Required(datetime, default=datetime.now)  # Timestamp set at creation by default
    priority = Required(int, default=0, index="priority_asc")  # Integer priority with an index name
    odg = Required("ODG")  # Many-to-one relation to ODG (foreign key)

    def __str__(self):
        # Human-readable representation used when printing or joining tasks.
        # Uses emoji to provide a compact display format.
        return f"📋 {self.text}\n👤 {self.created_by}"

class ODG(db.Entity):
    # ODG entity/table representing a chat/thread context that can contain multiple Tasks.
    chatId = Required(int, sql_type='BIGINT', size=64)  # Chat identifier stored as big integer
    threadId = Optional(int, sql_type='BIGINT', size=64)  # Optional thread identifier (nullable)
    tasks = Set(Task, reverse="odg")  # One-to-many relation: an ODG has many Tasks; reverse points to Task.odg

    def __str__(self):
        # Return a message when there are no tasks, otherwise join the string repr of tasks.
        # Tasks are ordered by their creation timestamp.
        if self.tasks.is_empty():
            return "ODG list is empty."
        # Correzione: converte il risultato in una lista per renderlo iterabile
        return "\n\n".join(str(task) for task in list(self.tasks.order_by(Task.created_at)))

    def reset(self):
        # Remove all tasks associated with this ODG.
        # First delete each Task entity from the DB, then clear the Set relation.
        for task in self.tasks:
            task.delete()
        self.tasks.clear()

    def remove_task(self, task_idx: int) -> bool:
        # Remove a single task by its index in the ordered-by-created_at list.
        # Uses Pony's limit(offset=...) to select the task at the given zero-based index.
        # Returns True if a task was found and deleted, False otherwise.
        task = list(self.tasks.order_by(Task.created_at).limit(1, offset=task_idx))
        if task:
            task[0].delete()
            return True
        return False

# Generate mapping between the above entities and the actual database tables.
# create_tables=True ensures tables are created in the database if they don't exist.
db.generate_mapping(create_tables=True)
