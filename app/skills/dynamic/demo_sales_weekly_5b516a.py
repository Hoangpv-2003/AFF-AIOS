from __future__ import annotations
import datetime
from collections import defaultdict

def run(input_data: dict | None = None) -> dict:
    if input_data is None:
        return {}
    
    sales = input_data.get('sales', [])
    weekly_totals = defaultdict(float)
    
    for sale in sales:
        date_str = sale.get('date')
        amount = sale.get('amount', 0)
        if not date_str:
            continue
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            year, week, _ = date.isocalendar()
            weekly_totals[(year, week)] += amount
        except ValueError:
            continue
    
    weekly_list = []
    for (year, week), total in weekly_totals.items():
        week_start = datetime.date(year, 1, 1) + datetime.timedelta(days=(week - 1)*7)
        week_end = week_start + datetime.timedelta(days=6)
        weekly_list.append({
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'total_sales': total
        })
    
    weekly_list.sort(key=lambda x: x['week_start'])
    
    total_sales = sum(item['total_sales'] for item in weekly_list)
    num_weeks = len(weekly_list)
    average_sales = total_sales / num_weeks if num_weeks > 0 else 0
    start_date = weekly_list[0]['week_start'] if num_weeks > 0 else None
    end_date = weekly_list[-1]['week_end'] if num_weeks > 0 else None
    
    summary = {
        'total_sales': total_sales,
        'average_weekly_sales': average_sales,
        'number_of_weeks': num_weeks,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return {
        'weekly_sales': weekly_list,
        'summary': summary
    }
