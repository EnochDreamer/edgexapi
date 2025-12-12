from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    def save(self):
        db.session.add(self)
        db.session.commit()
    def remove(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self) -> str:
        return f"<User {self.username}>"

