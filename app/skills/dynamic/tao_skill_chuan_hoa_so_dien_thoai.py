from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    """
    This function runs the Tao skill chuan hoa so dien thoai.

    Args:
        input_data (dict, optional): The input data for this skill. Defaults to None.

    Returns:
        dict: A dictionary containing the result of the skill.
    """

    # Define the objective and confidence level
    objective = "Tao skill chuan hoa so dien thoai"
    confidence_level = 0.85

    # Define the steps required for this skill
    steps = [
        "analyze requirements",
        "implement solution",
        "add tests",
        "integrate with system",
        "document usage",
        "deploy skill"
    ]

    # Return the result as a dictionary
    return {
        'objective': objective,
        'steps': steps,
        'confidence': confidence_level
    }
