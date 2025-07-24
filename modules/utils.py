import re


def pretty_time(hours: float) -> str:
    int_hours = int(hours)
    minutes = int((hours - int_hours) * 60)
    if hours < 1:
        return f"{minutes} minutes"
    return f"{int_hours}h {minutes}min"


def find_tags(text: str) -> set[str]:
    return set(re.findall(r'@\w+', text))
