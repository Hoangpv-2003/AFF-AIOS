from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    import csv
    total_revenue = 0.0
    entries = []
    try:
        with open('sample.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                date = row['date']
                revenue = float(row['revenue'])
                entries.append({'date': date, 'revenue': revenue})
                total_revenue += revenue
    except Exception as e:
        return {'error': str(e)}
    
    report = {
        'total_revenue': total_revenue,
        'entries': entries
    }
    summary = {
        'total_revenue': total_revenue
    }
    
    return {
        'report': report,
        'summary': summary
    }
