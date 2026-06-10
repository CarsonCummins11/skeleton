import logging

from lib import db
from models.users import User


async def insert_test_data():
    try:
        async with await db.open_db_connection() as connection:
            logging.info("Inserting test data")
            await User(
                username="test",
                hashed_password="$2b$12$zXGkaMKqwzeLrEtij8eOn..ib81Ckyav.cTC/s7v3dqPJVlI8iRC.",  # password: "test"
                full_name="Test User",
                profile_image_url="",
            ).create(connection)
    except Exception:
        logging.info("Test user already exists, skipping")
