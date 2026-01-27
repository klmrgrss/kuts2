# app/logic/helpers.py
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List, Tuple

def calculate_total_experience_years(periods: List[Tuple[date, date]]) -> float:
    """
    Calculates the total number of unique months of work experience from a list of
    start and end date tuples, eliminating overlaps.

    Args:
        periods: A list of tuples, where each tuple is a (start_date, end_date).

    Returns:
        The total experience in years as a float (e.g., 3.5 for 3 years and 6 months).
    """
    if not periods:
        return 0.0

    # Sort periods by start date to make merging easier
    periods.sort(key=lambda p: p[0])

    merged = [periods[0]]
    for current_start, current_end in periods[1:]:
        last_start, last_end = merged[-1]

        # If the current period overlaps with the last one in the merged list...
        if current_start <= last_end:
            # ...extend the merged period to cover the later of the two end dates.
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            # Otherwise, it's a new, distinct period.
            merged.append((current_start, current_end))

    # Calculate the total number of months from the merged, non-overlapping periods
    total_months = 0
    for start, end in merged:
        # relativedelta gives us the difference in years and months
        delta = relativedelta(end, start)
        total_months += delta.years * 12 + delta.months + 1 # Add 1 to include the start month

    return round(total_months / 12.0, 2)

def format_duration_est(years_float: float) -> str:
    """Formats 2.5 -> '2a 6k'"""
    if not years_float: return "0a 0k"
    
    total_months = int(round(years_float * 12))
    years = total_months // 12
    months = total_months % 12
    
    parts = []
    if years > 0: parts.append(f"{years}a")
    if months > 0: parts.append(f"{months}k")
    
    return " ".join(parts) if parts else "0k"

def construct_workex_header(req_str: str, provided_raw_str: str, accepted_years: float) -> str:
    """
    Constructs the standardized header string:
    'Nõutav: X | Esitatud: Y | Vastavaks tunnistatud: Z'
    Handles parsing raw provided strings like '3.0a' or 'Esitatud: 3.5a' into clean '3a 6k'.
    """
    import re
    
    # 1. Parse Provided Value
    user_sum_val = 0.0
    try:
         target_str = provided_raw_str or ""
         if "Esitatud:" in target_str:
             m = re.search(r'Esitatud:\s*([^|]+)', target_str)
             if m: target_str = m.group(1)
         
         m_val = re.search(r'([\d\.]+)', target_str)
         if m_val: user_sum_val = float(m_val.group(1))
    except: pass
    
    user_sum_fmt = format_duration_est(user_sum_val)
    accepted_fmt = format_duration_est(accepted_years)
    
    return f"Nõutav: {req_str} | Esitatud: {user_sum_fmt} | Vastavaks tunnistatud: {accepted_fmt}"