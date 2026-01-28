from auth.utils import get_birthdate_from_national_id

test_cases = [
    ("39005150005", "1990-05-15"),  # Male, 20th cent
    ("49005150005", "1990-05-15"),  # Female, 20th cent
    ("50505050005", "2005-05-05"),  # Male, 21st cent
    ("60505050005", "2005-05-05"),  # Female, 21st cent
    ("10101010005", "1801-01-01"),  # Male, 19th cent (rare but valid format logic)
]

print("Testing ID parsing...")
for pid, expected in test_cases:
    result = get_birthdate_from_national_id(pid)
    print(f"ID: {pid} -> {result} [{'PASS' if result == expected else 'FAIL'}]")
    if result != expected:
        print(f"  Expected: {expected}, Got: {result}")

print("Done.")
