from datetime import datetime  # used for timestamps on Task creation
from pony.orm import Database, Required, Optional, Set  # Pony ORM constructs
import tomllib
import logging

# Load configuration from config.ini
with open("data/config.ini", "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error(f"modules/database - Error parsing data/config.ini: {e}")
        exit(1)

# Create a Database object connected to a SQLite file.
db = Database()
db.bind(provider="sqlite", filename=config['Paths']['DatabasePath'], create_db=True)

class Task(db.Entity):
    """ Task entity/table representing individual tasks in an ODG. """

    text = Required(str)  # The task text/content
    created_by = Required(str)  # Username or identifier of the creator
    created_at = Required(datetime, default=datetime.now)  # Timestamp set at creation by default
    priority = Required(int, default=0, index="priority_asc")  # Integer priority with an index name
    odg = Required("ODG")  # Many-to-one relation to ODG (foreign key)

    def __str__(self):
        """ String representation of the Task for display purposes. """

        return f"📋 {self.text}\n👤 {self.created_by}"

class ODG(db.Entity):
    """ ODG entity/table representing a collection of tasks for a chat/thread. """
    
    chatId = Required(int, sql_type='BIGINT', size=64)  # Chat identifier stored as big integer
    threadId = Optional(int, sql_type='BIGINT', size=64)  # Optional thread identifier (nullable)
    tasks = Set(Task, reverse="odg")  # One-to-many relation: an ODG has many Tasks; reverse points to Task.odg

    def __str__(self):
        """ String representation of the ODG and its tasks for display purposes. """

        if self.tasks.is_empty():
            return "ODG list is empty."
        return "\n\n".join(str(task) for task in list(self.tasks.order_by(Task.created_at)))

    def reset(self):
        """ Remove all tasks from this ODG. """
        
        for task in self.tasks:
            task.delete()
        self.tasks.clear()

    def remove_task(self, task_idx: int) -> bool:
        """ Remove a specific task by its index in the ordered list of tasks. """

        task = list(self.tasks.order_by(Task.created_at).limit(1, offset=task_idx))
        if task:
            task[0].delete()
            return True
        return False

# Generate mapping between the above entities and the actual database tables.
db.generate_mapping(create_tables=True)
