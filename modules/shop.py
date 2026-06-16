from datetime import datetime  # used for timestamps on Task creation
from pony.orm import Database, Required, Optional, Set  # Pony ORM constructs
import tomllib
import logging
import os
import random

# Load configuration from config.ini
with open(os.getenv("CONFIG_PATH"), "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error(f"modules/shop - Error parsing data/config.ini: {e}")
        exit(1)

# Create a Database object connected to a PostgreSQL database.
db = Database()
db.bind(provider="postgres", user=config['Database']['DB_USER'], password=os.getenv("DB_PASSWORD"), host=config['Database']['DB_HOST'], port=config['Database']['DB_PORT'], database=config['Database']['DB_NAME'])

class Item(db.Entity):
    """ Item entity/table representing individual items in a SHOP. """

    text = Required(str)  # The item text/content
    created_by = Required(str)  # Username or identifier of the creator
    created_at = Required(datetime, default=datetime.now)  # Timestamp set at creation by default
    priority = Required(int, default=0)  # Integer priority with an index name
    shop = Required("SHOP")  # Many-to-one relation to SHOP (foreign key)

    def __str__(self):
        """ String representation of the Item for display purposes. """

        return f"{random.choice(['🪑', '📦', '🎁', '🧸', '🛍️', '📚', '🍀', '⚙️', '🚪', '🎨', '🔨', '🏎️', '🎹', '⚽️', '🎾', '✈️', '💻', '🖨️', '🕰️', '📻', '💾', '🧯', '📞' , '💣', '🪓', '🪚', '🎸', '🪏', '🧱', '🪜', '🧽', '🪣', '⚰️', '🔩', '💸'])} {self.text}"

class SHOP(db.Entity):
    """ SHOP entity/table representing a collection of items for a chat/thread. """
    
    chatId = Required(int, sql_type='BIGINT', size=64)  # Chat identifier stored as big integer
    threadId = Optional(int, sql_type='BIGINT', size=64)  # Optional thread identifier (nullable)
    items = Set(Item, reverse="shop")  # One-to-many relation: a SHOP has many Items; reverse points to Item.shop

    def __str__(self):
        """ String representation of the SHOP and its items for display purposes. """

        if self.items.is_empty():
            return "Shop list is empty."
        return "\n\n".join(str(item) for item in list(self.items.order_by(Item.created_at)))

    def reset(self):
        """ Remove all items from this SHOP. """
        
        for item in self.items:
            item.delete()
        self.items.clear()

    def remove_item(self, item_idx: int) -> bool:
        """ Remove a specific item by its index in the ordered list of items. """

        item = list(self.items.order_by(Item.created_at).limit(1, offset=item_idx))
        if item:
            item[0].delete()
            return True
        return False

# Generate mapping between the above entities and the actual database tables.
db.generate_mapping(create_tables=True)
