from decimal import Decimal

from ..extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    

    def __repr__(self) -> str:
        return f"<Product {self.name}>"

