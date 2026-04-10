"""init products and stock movements

Revision ID: 0001_init
Revises: 
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("uq_products_sku", "products", ["sku"], unique=True)

    movement_type = sa.Enum("receive", "ship", "adjust", name="movement_type")
    adjust_direction = sa.Enum("increase", "decrease", name="adjust_direction")

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", movement_type, nullable=False),
        sa.Column("direction", adjust_direction, nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])
    op.create_index("ix_stock_movements_product_id_created_at", "stock_movements", ["product_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_stock_movements_product_id_created_at", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product_id", table_name="stock_movements")
    op.drop_table("stock_movements")

    op.drop_index("uq_products_sku", table_name="products")
    op.drop_table("products")

    sa.Enum(name="movement_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="adjust_direction").drop(op.get_bind(), checkfirst=True)

