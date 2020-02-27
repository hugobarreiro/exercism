from flask import (
    Flask,
    jsonify,
    request
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
db = SQLAlchemy(app)

import models
db.create_all()


def _build_users_objects(users):
    objs = {'users': [_build_user_object(user) for user in users]}
    objs['users'].sort(key=lambda u: u['name'])
    return objs


def _build_user_object(user):

    owes = dict(models.Loan.query.with_entities(
        models.User.name,
        -db.func.sum(models.Loan.amount).label('amount')
    )\
        .join(models.User, models.Loan.lender)\
        .group_by(models.Loan.lender_id)\
        .filter(models.Loan.borrower_id == user.id)\
        .all()
    )

    owed_by = dict(models.Loan.query.with_entities(
        models.User.name,
        db.func.sum(models.Loan.amount).label('amount')
    )\
        .join(models.User, models.Loan.borrower)\
        .group_by(models.Loan.borrower_id)\
        .filter(models.Loan.lender_id == user.id)\
        .all()
    )

    credit = {
        u: owed_by.get(u, 0) + owes.get(u, 0)
        for u in set(owes) | set(owed_by)
    }
    owes = {}
    owed_by = {}
    balance = 0

    for u, val in credit.items():
        if val > 0:
            owed_by[u] = val
        elif val < 0:
            owes[u] = -val
        balance += val

    return dict(
        name=user.name,
        owes=owes,
        owed_by=owed_by,
        balance=balance
    )


@app.route('/users', methods=['GET'])
def get_users():
    if request.form:
        if 'users' in request.form:
            users = [models.User.query.filter_by(name=user).first() for user in request.form.getlist('users')]
        else:
            return jsonify({'error': 'Bad payload syntax.'}), 400
    else:
        users = models.User.query.all()
    return jsonify(_build_users_objects(users))


@app.route('/add', methods=['POST'])
def add_user():
    if request.form and 'user' in request.form:
        user = models.User.query.filter_by(name=request.form['user']).first()
        if user is None:
            user = models.User(name=request.form['user'])
            db.session.add(user)
            db.session.commit()
        return jsonify(_build_user_object(user))

    return jsonify({'error': 'No user was informed'}), 400


@app.route('/iou', methods=['POST'])
def add_loan():
    if request.form:
        lender = models.User.query.filter_by(name=request.form['lender']).first()
        borrower = models.User.query.filter_by(name=request.form['borrower']).first()
        amount = request.form.get('amount', type=float)

        db.session.add(models.Loan(
            lender=lender,
            borrower=borrower,
            amount=amount
        ))
        db.session.commit()

        return jsonify(_build_users_objects([lender, borrower]))

    return jsonify({'error': 'No loan informed.'}), 400


if __name__ == '__main__':
    app.run(
        debug=True,
        port=8080
    )