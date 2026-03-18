from __future__ import annotations
import pandas as pd
import numpy as np

def thong_ke_doanh_thu(input_data: dict | None = None) -> dict:
    """
    Function to calculate sales revenue per week and generate a detailed report.

    Args:
    input_data (dict): Input data for calculation, expected to contain columns 'date', 'revenue'.

    Returns:
    dict: A dictionary containing the result of the calculation.
    """

    # Set default values
    if input_data is None:
        input_data = {}

    # Load data from input
    df = pd.DataFrame(input_data.get('data', []))

    # Check for missing columns
    required_columns = ['date', 'revenue']
    if not all(column in df.columns for column in required_columns):
        return {
            "error": f"Missing required columns: {required_columns}",
            "result": None
        }

    # Convert date to datetime and extract week number
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week

    # Group data by week and calculate total revenue per week
    weekly_revenue = df.groupby('week')['revenue'].sum().reset_index()

    # Generate a detailed report
    report = {
        "title": "Sales Revenue by Week",
        "data": weekly_revenue.to_dict(orient='records')
    }

    return {
        'result': report,
        'status': 200,
        'message': 'Success'
    }

def run(input_data: dict | None = None) -> dict:
    """
    Main function to execute the skill.

    Args:
    input_data (dict): Input data for calculation, expected to contain a list of dictionaries with columns 'date', 'revenue'.

    Returns:
    dict: A dictionary containing the result of the calculation.
    """

    return thong_ke_doanh_thu(input_data)
