
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))
from database import setup_database

def check_eval_table():
    db = setup_database()
    print(f"DB Object: {db}")
    
    if 'evaluations' in db.t:
        evals = db.t.evaluations
        print(f"Table 'evaluations' found.")
        print(f"PK Property: {evals.pks}")
        print(f"Columns: {evals.columns}")
        
        # Check rows
        rows = list(evals.rows)
        print(f"Row count: {len(rows)}")
        if rows:
            print(f"Sample row: {rows[0]}")
            
        # Try to insert and get
        test_id = "test_pk_check"
        try:
            print("Attempting test insert...")
            evals.insert({"qual_id": test_id, "evaluator_email": "test", "evaluation_state_json": "{}"}, pk='qual_id', replace=True)
            print("Insert success.")
            
            print("Attempting test get...")
            rec = evals.get(test_id)
            print(f"Get success: {rec}")
            
            # Clean up
            evals.delete(test_id)
        except Exception as e:
            print(f"Test operation failed: {e}")
            import traceback
            traceback.print_exc()

    else:
        print("Table 'evaluations' NOT found in db.t")

if __name__ == "__main__":
    check_eval_table()
