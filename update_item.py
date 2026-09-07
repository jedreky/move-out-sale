import argparse
from src.db_utils import get_connection

parser = argparse.ArgumentParser(description="Update item price and priority.")
parser.add_argument("item_id", type=int)
parser.add_argument("--price", type=int)
parser.add_argument("--priority", type=int)
args = parser.parse_args()

if args.price is None and args.priority is None:
    parser.error("Specify at least one of --price or --priority.")

with get_connection() as conn:
    row = conn.execute("SELECT id, price, priority FROM items WHERE id = ?", (args.item_id,)).fetchone()
    if row is None:
        print(f"No item with id {args.item_id}.")
        raise SystemExit(1)

    item_id, old_price, old_priority = row
    new_price = args.price if args.price is not None else old_price
    new_priority = args.priority if args.priority is not None else old_priority

    conn.execute("UPDATE items SET price = ?, priority = ? WHERE id = ?", (new_price, new_priority, item_id))

print(f"Item {item_id}: price {old_price} -> {new_price}, priority {old_priority} -> {new_priority}")
