from __future__ import annotations

import os
import random

from sqlalchemy import text

from app.db.core import make_db, get_session
from app.db.models import AdjustDirection, MovementType, Product, StockMovement


def seed():
    db = make_db(os.environ.get("DATABASE_URL"))
    session = get_session(db)
    try:
        # Reset tables for deterministic demo data.
        session.execute(text("TRUNCATE TABLE stock_movements RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE"))
        session.commit()

        products = [
            Product(sku="SKU-1001", name="USB-C Cable (1m)", low_stock_threshold=15),
            Product(sku="SKU-1002", name="Mechanical Keyboard", low_stock_threshold=5),
            Product(sku="SKU-1003", name="27in Monitor", low_stock_threshold=3),
            Product(sku="SKU-1004", name="Laptop Stand", low_stock_threshold=8),
            Product(sku="SKU-1005", name="Wireless Mouse", low_stock_threshold=10),
        ]
        session.add_all(products)
        session.commit()

        rng = random.Random(42)

        for p in products:
            # Start with a receive.
            receive_qty = rng.randint(1, 35)
            session.add(
                StockMovement(product_id=p.id, type=MovementType.receive, quantity=receive_qty, note="Initial stock")
            )
            session.commit()

            # Add a few random movements.
            for i in range(rng.randint(8, 20)):
                kind = rng.choice(["ship", "receive", "adjust"])
                qty = rng.randint(1, 12)
                if kind == "receive":
                    session.add(
                        StockMovement(
                            product_id=p.id,
                            type=MovementType.receive,
                            quantity=qty,
                            note=f"Supplier delivery #{100+i}",
                        )
                    )
                elif kind == "ship":
                    # Keep stock non-negative by shipping at most current stock.
                    current = int(
                        session.execute(
                            text(
                                """
                                select coalesce(sum(
                                  case
                                    when type='receive' then quantity
                                    when type='ship' then -quantity
                                    when type='adjust' and direction='increase' then quantity
                                    when type='adjust' and direction='decrease' then -quantity
                                    else 0
                                  end
                                ), 0) as stock
                                from stock_movements
                                where product_id = :pid
                                """
                            ),
                            {"pid": p.id},
                        ).scalar_one()
                    )
                    if current <= 0:
                        continue
                    ship_qty = min(qty, current)
                    session.add(
                        StockMovement(
                            product_id=p.id,
                            type=MovementType.ship,
                            quantity=ship_qty,
                            note=f"Customer order #{500+i}",
                        )
                    )
                else:
                    direction = rng.choice([AdjustDirection.increase, AdjustDirection.decrease])
                    if direction == AdjustDirection.decrease:
                        current = int(
                            session.execute(
                                text(
                                    """
                                    select coalesce(sum(
                                      case
                                        when type='receive' then quantity
                                        when type='ship' then -quantity
                                        when type='adjust' and direction='increase' then quantity
                                        when type='adjust' and direction='decrease' then -quantity
                                        else 0
                                      end
                                    ), 0) as stock
                                    from stock_movements
                                    where product_id = :pid
                                    """
                                ),
                                {"pid": p.id},
                            ).scalar_one()
                        )
                        if current <= 0:
                            continue
                        qty = min(qty, current)
                    session.add(
                        StockMovement(
                            product_id=p.id,
                            type=MovementType.adjust,
                            direction=direction,
                            quantity=qty,
                            note="Cycle count adjustment",
                        )
                    )

                session.commit()

        print("Seeded demo data successfully.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()

