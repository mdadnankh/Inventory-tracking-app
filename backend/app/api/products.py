from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.db.core import get_session
from app.db.models import AdjustDirection, MovementType, Product, StockMovement
from app.schemas.movements import MovementCreate
from app.schemas.products import ProductCreate, ProductUpdate

bp = Blueprint("products", __name__, url_prefix="/api")


def _parse(model, payload):
    try:
        return model.model_validate(payload)
    except ValidationError as e:
        raise ApiError(code="validation_error", message="Invalid request", status=400, details=e.errors())


def _movement_delta(m: MovementCreate) -> int:
    if m.type == "receive":
        return m.quantity
    if m.type == "ship":
        return -m.quantity
    if m.type == "adjust":
        return m.quantity if m.direction == "increase" else -m.quantity
    raise ApiError(code="validation_error", message="Invalid movement type", status=400)


def _current_stock_expr():
    return func.coalesce(
        func.sum(
            case(
                (StockMovement.type == MovementType.receive, StockMovement.quantity),
                (StockMovement.type == MovementType.ship, -StockMovement.quantity),
                (
                    (StockMovement.type == MovementType.adjust) & (StockMovement.direction == AdjustDirection.increase),
                    StockMovement.quantity,
                ),
                (
                    (StockMovement.type == MovementType.adjust) & (StockMovement.direction == AdjustDirection.decrease),
                    -StockMovement.quantity,
                ),
                else_=0,
            )
        ),
        0,
    )


def get_current_stock(session, product_id: int) -> int:
    stmt = select(_current_stock_expr()).where(StockMovement.product_id == product_id)
    return int(session.execute(stmt).scalar_one())


@bp.get("/products")
def list_products():
    db = current_app.config["db"]
    session = get_session(db)
    try:
        stock = _current_stock_expr().label("current_stock")
        stmt = (
            select(Product, stock)
            .outerjoin(StockMovement, StockMovement.product_id == Product.id)
            .group_by(Product.id)
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


@bp.post("/products")
def create_product():
    payload = request.get_json(silent=True) or {}
    data = _parse(ProductCreate, payload)

    db = current_app.config["db"]
    session = get_session(db)
    try:
        p = Product(sku=data.sku.strip(), name=data.name.strip(), low_stock_threshold=data.low_stock_threshold)
        session.add(p)
        session.commit()
        return (
            jsonify(
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "low_stock_threshold": p.low_stock_threshold,
                    "current_stock": 0,
                }
            ),
            201,
        )
    except IntegrityError:
        session.rollback()
        raise ApiError(code="conflict", message="SKU already exists", status=409)
    finally:
        session.close()


@bp.patch("/products/<int:product_id>")
def update_product(product_id: int):
    payload = request.get_json(silent=True) or {}
    data = _parse(ProductUpdate, payload)

    db = current_app.config["db"]
    session = get_session(db)
    try:
        p = session.get(Product, product_id)
        if not p:
            raise ApiError(code="not_found", message="Product not found", status=404)
        if data.name is not None:
            p.name = data.name.strip()
        if data.low_stock_threshold is not None:
            p.low_stock_threshold = data.low_stock_threshold
        session.commit()
        stock = get_current_stock(session, product_id)
        return jsonify(
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "low_stock_threshold": p.low_stock_threshold,
                "current_stock": stock,
            }
        )
    finally:
        session.close()


@bp.get("/products/<int:product_id>/movements")
def list_movements(product_id: int):
    limit_raw = request.args.get("limit", "50")
    cursor_raw = request.args.get("cursor")
    try:
        limit = int(limit_raw)
    except ValueError:
        raise ApiError(code="validation_error", message="limit must be an integer", status=400)
    if limit < 1 or limit > 200:
        raise ApiError(code="validation_error", message="limit must be between 1 and 200", status=400)

    cursor = None
    if cursor_raw is not None:
        try:
            cursor = int(cursor_raw)
        except ValueError:
            raise ApiError(code="validation_error", message="cursor must be an integer", status=400)

    db = current_app.config["db"]
    session = get_session(db)
    try:
        p = session.get(Product, product_id)
        if not p:
            raise ApiError(code="not_found", message="Product not found", status=404)

        stmt = select(StockMovement).where(StockMovement.product_id == product_id)
        if cursor is not None:
            # Cursor is the last seen movement id; fetch "older" movements (smaller ids).
            stmt = stmt.where(StockMovement.id < cursor)
        stmt = stmt.order_by(StockMovement.id.desc()).limit(limit + 1)
        moves = [m for (m,) in session.execute(stmt).all()]
        has_more = len(moves) > limit
        moves = moves[:limit]
        next_cursor = moves[-1].id if has_more and moves else None

        out = [
            {
                "id": m.id,
                "product_id": m.product_id,
                "type": m.type.value,
                "direction": m.direction.value if m.direction else None,
                "quantity": m.quantity,
                "note": m.note,
                "created_at": m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at),
            }
            for m in moves
        ]
        return jsonify({"items": out, "next_cursor": next_cursor})
    finally:
        session.close()


@bp.post("/products/<int:product_id>/movements")
def create_movement(product_id: int):
    payload = request.get_json(silent=True) or {}
    data = _parse(MovementCreate, payload)
    delta = _movement_delta(data)

    db = current_app.config["db"]
    session = get_session(db)
    try:
        p = session.get(Product, product_id)
        if not p:
            raise ApiError(code="not_found", message="Product not found", status=404)

        current = get_current_stock(session, product_id)
        if current + delta < 0:
            raise ApiError(
                code="invariant_violation",
                message="Movement would make stock negative",
                status=400,
                details={"current_stock": current, "delta": delta},
            )

        m = StockMovement(
            product_id=product_id,
            type=MovementType(data.type),
            direction=AdjustDirection(data.direction) if data.direction else None,
            quantity=data.quantity,
            note=data.note,
        )
        session.add(m)
        session.commit()

        return (
            jsonify(
                {
                    "id": m.id,
                    "product_id": m.product_id,
                    "type": m.type.value,
                    "direction": m.direction.value if m.direction else None,
                    "quantity": m.quantity,
                    "note": m.note,
                    "created_at": m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at),
                    "current_stock": current + delta,
                }
            ),
            201,
        )
    finally:
        session.close()

