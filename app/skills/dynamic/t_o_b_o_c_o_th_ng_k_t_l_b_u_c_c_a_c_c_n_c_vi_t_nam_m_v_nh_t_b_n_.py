from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    """Generate election turnout report for Vietnam, USA, Japan"""
    # Default sample data if no input provided
    if input_data is None:
        input_data = {
            "vietnam": {"turnout_rate": 92.3, "year": 2023, "eligible_voters": 90000000},
            "usa": {"turnout_rate": 62.4, "year": 2020, "eligible_voters": 240000000},
            "japan": {"turnout_rate": 56.7, "year": 2023, "eligible_voters": 85000000}
        }
    
    # Data processing
    processed_data = []
    for country, stats in input_data.items():
        processed_data.append({
            "country": country,
            "turnout_rate": round(stats["turnout_rate"], 1),
            "year": stats["year"],
            "eligible_voters": stats["eligible_voters"],
            "turnout_percentage": f"{stats['turnout_rate']}%",
            "status": "completed" if stats["turnout_rate"] > 50 else "low"
        })
    
    # Analysis
    total_voters = sum(d["eligible_voters"] for d in processed_data)
    avg_turnout = round(sum(d["turnout_rate"] for d in processed_data) / len(processed_data), 1)
    
    # Report structure
    return {
        "report": {
            "title": "Election Turnout Report",
            "date": "2023-10-15",
            "countries": ["Vietnam", "USA", "Japan"],
            "total_eligible_voters": total_voters,
            "average_turnout_rate": avg_turnout,
            "highest_turnout": max(d["turnout_rate"] for d in processed_data),
            "lowest_turnout": min(d["turnout_rate"] for d in processed_data)
        },
        "data": processed_data,
        "analysis": {
            "vietnam": {
                "status": "high",
                "comparison": "Above global average",
                "notes": "Record high participation in 2023 election"
            },
            "usa": {
                "status": "medium",
                "comparison": "Below global average",
                "notes": "Historically lower turnout compared to other nations"
            },
            "japan": {
                "status": "low",
                "comparison": "Significantly below global average",
                "notes": "Continues to show low voter engagement"
            }
        },
        "summary": {
            "total_eligible_voters": total_voters,
            "average_turnout_rate": avg_turnout,
            "highest_turnout": max(d["turnout_rate"] for d in processed_data),
            "lowest_turnout": min(d["turnout," for d in processed_data),
            "report_status": "completed"
        }
    }
