from pony.orm import Database, Required, Optional, Set, PrimaryKey, select
import tomllib
import logging

# Load configuration from config.ini
with open("data/config.ini", "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error(f"modules/quiz - Error parsing data/config.ini: {e}")
        exit(1)

# Create a Database object connected to a SQLite file.
db = Database()
db.bind(provider='sqlite', filename=config['Paths']['QuizDBPath'], create_db=True)

class Events(db.Entity):
    """ Represents an event which can contain multiple quizzes. """

    event_id = PrimaryKey(int, auto=True)  # Unique identifier for the event.
    short_name = Required(str)  # A short name or abbreviation for the event.
    event_name = Required(str)  # The full name of the event.
    country = Optional(str)  # The country where the event takes place.
    website = Optional(str)  # The official website of the event.
    quizzes = Set('Quiz')  # A collection of quizzes associated with this event.

class Quiz(db.Entity):
    """ Represents a single quiz, which belongs to one or more events. """

    quiz_id = PrimaryKey(int, auto=True)  # Unique identifier for the quiz.
    year = Optional(str)  # The year the quiz was held.
    class_ = Optional(str, column='class')  # The class or category of the quiz. 'column' is used to avoid conflict with Python's 'class' keyword.
    date = Optional(str)  # The specific date of the quiz.
    status = Optional(str)  # The current status of the quiz (e.g., 'upcoming', 'completed').
    information = Optional(str)  # Additional information about the quiz.
    questions = Set('Questions')  # A collection of questions in this quiz.
    events = Set(Events)  # A collection of events this quiz is part of.

class Questions(db.Entity):
    """ Represents a single question within a quiz. """

    id = Required(int)  # An identifier for the question, unique within a quiz.
    quiz = Required(Quiz)  # The quiz this question belongs to.
    PrimaryKey(id, quiz)  # Composite primary key using question id and quiz.
    text = Required(str)  # The text of the question.
    type = Optional(str)  # The type of question (e.g., 'multiple_choice').
    position_index = Optional(int)  # The position of the question in the quiz.
    answers = Set('Answers')  # A collection of possible answers for this question.
    images = Set('Images')  # A collection of images associated with this question.

    def isValid(self):
        """
        Validates the question based on its answers.
        A question is valid if it has:
            - Between 2 and 12 answers.
            - Exactly one correct answer.
            - All answer texts are 100 characters or less.
        """

        if 2 <= self.answers.count() <= 12 and sum(1 for a in self.answers if a.is_correct) == 1 and all(len(a.answer_text) <= 100 for a in self.answers):
            return True
        return False

class Answers(db.Entity):
    """ Represents a single answer to a question. """

    answer_id = PrimaryKey(int, auto=True)  # Unique identifier for the answer.
    question = Required(Questions)  # The question this answer belongs to.
    answer_text = Required(str)  # The text of the answer.
    is_correct = Required(bool)  # Flag indicating if this is the correct answer.

class Images(db.Entity):
    """ Represents an image associated with a question. """

    id = PrimaryKey(int, auto=True)  # Unique identifier for the image.
    path = Required(str)  # The file path or URL to the image.
    question = Required(Questions)  # The question this image is associated with.
    
# Generate mapping between the above entities and the actual database tables.
db.generate_mapping(create_tables=True)
