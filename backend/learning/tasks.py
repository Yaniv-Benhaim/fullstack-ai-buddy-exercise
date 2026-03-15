from celery import shared_task


@shared_task
def generate_ai_nudge(user_id: int, module_id: int):
    """
    Generate an AI-powered nudge after a user completes a learning module.
    """
    # TODO (Step 1): Implement this task — see INSTRUCTIONS.md Step 1
    pass
