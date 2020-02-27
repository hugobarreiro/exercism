from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lender = db.relationship('User', foreign_keys=[lender_id])
    borrower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    borrower = db.relationship('User', foreign_keys=[borrower_id])
    amount = db.Column(db.Float)
