import argparse
import sqlite3
from pathlib import Path

from app.auth.policy import PolicyStore


def bootstrap(database_path: Path, user_id: str, display_name: str, matter_id: str | None) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    policy = PolicyStore(connection)
    policy.initialize()
    if not policy.user_exists(user_id):
        policy.add_user(user_id, display_name)
    if matter_id and not policy.matter_exists(matter_id):
        policy.create_matter(matter_id, user_id)
    connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a local development user and optional matter."
    )
    parser.add_argument("--database", type=Path, default=Path("data/legal_rag.sqlite3"))
    parser.add_argument("--user-id", default="demo-user")
    parser.add_argument("--display-name", default="Demo User")
    parser.add_argument("--matter-id", default="demo-matter")
    args = parser.parse_args()
    bootstrap(args.database, args.user_id, args.display_name, args.matter_id)
    print(f"Bootstrapped user '{args.user_id}'")
    if args.matter_id:
        print(f"Bootstrapped matter '{args.matter_id}'")


if __name__ == "__main__":
    main()
