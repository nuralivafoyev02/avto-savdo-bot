import aiosqlite
import json

from config import DB_FILE


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    phone TEXT,
                    username TEXT
                )
                '''
            )
            await db.execute(
                '''
                CREATE TABLE IF NOT EXISTS cars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    model TEXT,
                    price INTEGER,
                    condition TEXT,
                    transmission TEXT,
                    color TEXT,
                    mileage INTEGER,
                    region TEXT,
                    photo TEXT,
                    phone TEXT,
                    username TEXT,
                    photos TEXT,
                    status TEXT DEFAULT 'active',
                    channel_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sold_at TIMESTAMP
                )
                '''
            )

            await self._ensure_column(db, 'cars', 'photos', 'TEXT')
            await self._ensure_column(db, 'cars', 'status', "TEXT DEFAULT 'active'")
            await self._ensure_column(db, 'cars', 'channel_message_id', 'INTEGER')
            await self._ensure_column(db, 'cars', 'sold_at', 'TIMESTAMP')

            await db.commit()

    async def _ensure_column(self, db: aiosqlite.Connection, table: str, column: str, ddl: str) -> None:
        async with db.execute(f"PRAGMA table_info({table})") as cursor:
            rows = await cursor.fetchall()
        existing = {row[1] for row in rows}
        if column not in existing:
            await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    async def add_user(self, user_id: str, phone: str, username: str | None) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO users (user_id, phone, username) VALUES (?, ?, ?)',
                (user_id, phone, username),
            )
            await db.commit()

    async def get_user(self, user_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT user_id, phone, username FROM users WHERE user_id = ?',
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return {'user_id': row[0], 'phone': row[1], 'username': row[2]}

    async def add_car(self, car_data: dict) -> int:
        photos = car_data.get('photos') or []
        photo = car_data.get('photo') or (photos[0] if photos else None)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                '''
                INSERT INTO cars (
                    user_id, model, price, condition, transmission,
                    color, mileage, region, photo, phone, username,
                    photos, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    car_data.get('user_id'),
                    car_data.get('model'),
                    car_data.get('price'),
                    car_data.get('condition'),
                    car_data.get('transmission'),
                    car_data.get('color'),
                    car_data.get('mileage'),
                    car_data.get('region'),
                    photo,
                    car_data.get('phone'),
                    car_data.get('username'),
                    json.dumps(photos, ensure_ascii=False),
                    'active',
                ),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def set_channel_message_id(self, car_id: int, message_id: int | None) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE cars SET channel_message_id = ? WHERE id = ?',
                (message_id, car_id),
            )
            await db.commit()

    async def get_car(self, car_id: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM cars WHERE id = ?',
                (car_id,),
            ) as cursor:
                columns = [column[0] for column in cursor.description]
                row = await cursor.fetchone()
                if not row:
                    return None
                return self._row_to_dict(columns, row)

    async def mark_car_sold(self, car_id: int, owner_user_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM cars WHERE id = ? AND user_id = ? AND status != 'sold'",
                (car_id, owner_user_id),
            ) as cursor:
                columns = [column[0] for column in cursor.description]
                row = await cursor.fetchone()
                if not row:
                    return None

            await db.execute(
                "UPDATE cars SET status = 'sold', sold_at = CURRENT_TIMESTAMP WHERE id = ?",
                (car_id,),
            )
            await db.commit()
            return self._row_to_dict(columns, row, override={'status': 'sold'})

    async def search_cars(
        self,
        model: str | None = None,
        price_min: int = 0,
        price_max: int = 999_999_999,
    ) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            query = (
                "SELECT * FROM cars "
                "WHERE status = 'active' AND price >= ? AND price <= ?"
            )
            params: list = [price_min, price_max]

            if model:
                query += ' AND model LIKE ?'
                params.append(f'%{model}%')

            query += ' ORDER BY id DESC'

            async with db.execute(query, params) as cursor:
                columns = [column[0] for column in cursor.description]
                rows = await cursor.fetchall()
                return [self._row_to_dict(columns, row) for row in rows]

    async def get_stats(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            total_users = await self._scalar(db, 'SELECT COUNT(*) FROM users')
            total_cars = await self._scalar(db, 'SELECT COUNT(*) FROM cars')
            active_cars = await self._scalar(db, "SELECT COUNT(*) FROM cars WHERE status = 'active'")
            sold_cars = await self._scalar(db, "SELECT COUNT(*) FROM cars WHERE status = 'sold'")
            today_ads = await self._scalar(
                db,
                "SELECT COUNT(*) FROM cars WHERE date(created_at) = date('now', 'localtime')",
            )

            async with db.execute(
                '''
                SELECT region, COUNT(*) AS cnt
                FROM cars
                GROUP BY region
                ORDER BY cnt DESC
                LIMIT 1
                '''
            ) as cursor:
                top_region_row = await cursor.fetchone()

        return {
            'total_users': int(total_users or 0),
            'total_cars': int(total_cars or 0),
            'active_cars': int(active_cars or 0),
            'sold_cars': int(sold_cars or 0),
            'today_ads': int(today_ads or 0),
            'top_region': top_region_row[0] if top_region_row else None,
            'top_region_count': int(top_region_row[1]) if top_region_row else 0,
        }

    async def get_recent_cars(self, limit: int = 5) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM cars ORDER BY id DESC LIMIT ?',
                (limit,),
            ) as cursor:
                columns = [column[0] for column in cursor.description]
                rows = await cursor.fetchall()
                return [self._row_to_dict(columns, row) for row in rows]

    async def _scalar(self, db: aiosqlite.Connection, query: str):
        async with db.execute(query) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    def _row_to_dict(self, columns: list[str], row: tuple, override: dict | None = None) -> dict:
        data = dict(zip(columns, row))
        raw_photos = data.get('photos')

        if raw_photos:
            try:
                data['photos'] = json.loads(raw_photos)
            except json.JSONDecodeError:
                data['photos'] = [data.get('photo')] if data.get('photo') else []
        else:
            data['photos'] = [data.get('photo')] if data.get('photo') else []

        if override:
            data.update(override)
        return data


db_manager = DatabaseManager(DB_FILE)
