from __future__ import annotations

import datetime
from collections import defaultdict

def run(input_data: dict | None = None) -> dict:
    if input_data is None:
        sales_data = []
    else:
        sales_data = input_data.get('sales', [])
    
    weekly_sales = []
    total_sales = 0
    
    week_groups = defaultdict(float)
    
    for sale in sales_data:
        date_str = sale.get('date')
        amount = sale.get('amount', 0)
        if not date_str:
            continue
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            year, week, _ = date.isocalendar()
            week_key = (year, week)
            week_groups[week_key] += amount
        except ValueError:
            continue
    
    for (year, week), total in week_groups.items():
        weekly_sales.append({
            'week': f'{year}-W{week:02d}',
            'total_sales': total
        })
        total_sales += total
    
    avg_weekly = total_sales / len(weekly_sales) if weekly_sales else 0
    
    return {
        'total_sales': total_sales,
        'average_weekly_sales': avg_weekly,
        'weekly_sales': weekly_sales,
        'summary': f'Total sales: {total_sales}, Average weekly: {avg_weekly:.2f}'
    }
