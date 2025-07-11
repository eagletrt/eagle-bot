def pretty_time(hours: float) -> str:
    int_hours = int(hours)
    minutes = int((hours - int_hours) * 60)
    if hours < 1:
        return f"{minutes} minutes"
    return f"{int_hours}h {minutes}min"
