# helpers for courses app

def calculate_progress(enrollment):
    """
    Placeholder: compute progress based on completed lessons.
    A full implementation requires a Progress model that tracks completed lessons per user.
    """
    total_lessons = 0
    completed = 0
    for module in enrollment.course.modules.all():
        total_lessons += module.lessons.count()
    if total_lessons == 0:
        return 0
    return round((completed / total_lessons) * 100, 2)
