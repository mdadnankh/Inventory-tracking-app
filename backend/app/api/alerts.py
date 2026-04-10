from __future__ import annotations

from flask import Blueprint, current_app, jsonify
from sqlalchemy import func, select

from app.db.core import get_session
from app.db.models import Product, StockMovement
from app.api.products import _current_stock_expr

bp = Blueprint("alerts", __name__, url_prefix="/api")


@bp.get("/alerts/low-stock")
def low_stock():
    db = current_app.config["db"]
    session = get_session(db)
    try:
        stock = _current_stock_expr().label("current_stock")
        stmt = (
            select(Product, stock)
            .outerjoin(StockMovement, StockMovement.product_id == Product.id)
            .group_by(Product.id)
            .having(func.coalesce(stock, 0) <= Product.low_stock_threshold)
            .order_by(Product.id.asc())
        )

        rows = session.execute(stmt).all()
        out = [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "low_stock_threshold": p.low_stock_threshold,
                "current_stock": int(s),
            }
            for (p, s) in rows
        ]
        return jsonify(out)
    finally:
        session.close()

