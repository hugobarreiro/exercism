import json
import unittest

from app import app, db, models


class IOUAppTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        db.drop_all()
        db.create_all()


class EmptyDBTest(IOUAppTest):

    def test_no_users(self):
        expected = {"users": []}

        response = self.app.get('/users')
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)

    def test_add_users(self):
        payload = {"user": "Adam"}
        expected = {"name": "Adam", "owes": {}, "owed_by": {}, "balance": 0.0}

        response = self.app.post('/add', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)


class TwoUsersTest(IOUAppTest):

    def setUp(self):
        super().setUp()
        db.session.add(models.User(name='Adam'))
        db.session.add(models.User(name='Bob'))
        db.session.commit()


class TwoUsersWithNoLendTest(TwoUsersTest):

    def test_get_single_user(self):
        payload = {"users": ['Bob']}
        expected = {"users": [{"name": "Bob", "owes": {}, "owed_by": {}, "balance": 0.0}]}

        response = self.app.get('/users', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)

    def test_both_users_have_0_balance(self):
        payload = {"lender": "Adam", "borrower": "Bob", "amount": 3.0}
        expected = {
            "users": [
                {"name": "Adam", "owes": {}, "owed_by": {"Bob": 3.0}, "balance": 3.0},
                {"name": "Bob", "owes": {"Adam": 3.0}, "owed_by": {}, "balance": -3.0},
            ]
        }

        response = self.app.post('/iou', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)


class TwoUsersWithLendTest(TwoUsersTest):

    def setUp(self):
        super().setUp()
        db.session.add(models.Loan(
            borrower=models.User.query.filter_by(name='Adam').first(),
            lender=models.User.query.filter_by(name='Bob').first(),
            amount=3.0
        ))
        db.session.commit()

    def test_lender_owes_borrower(self):
        payload = {"lender": "Adam", "borrower": "Bob", "amount": 2.0}
        expected = {
            "users": [
                {"name": "Adam", "owes": {"Bob": 1.0}, "owed_by": {}, "balance": -1.0},
                {"name": "Bob", "owes": {}, "owed_by": {"Adam": 1.0}, "balance": 1.0},
            ]
        }

        response = self.app.post('/iou', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)

    def test_lender_owes_borrower_less_than_new_loan(self):
        payload = {"lender": "Adam", "borrower": "Bob", "amount": 4.0}
        expected = {
            "users": [
                {"name": "Adam", "owes": {}, "owed_by": {"Bob": 1.0}, "balance": 1.0},
                {"name": "Bob", "owes": {"Adam": 1.0}, "owed_by": {}, "balance": -1.0},
            ]
        }

        response = self.app.post('/iou', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)

    def test_lender_owes_borrower_same_as_new_loan(self):
        payload = {"lender": "Adam", "borrower": "Bob", "amount": 3.0}
        expected = {
            "users": [
                {"name": "Adam", "owes": {}, "owed_by": {}, "balance": 0.0},
                {"name": "Bob", "owes": {}, "owed_by": {}, "balance": 0.0},
            ]
        }

        response = self.app.post('/iou', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)


class ThreeUsersTest(IOUAppTest):

    def setUp(self):
        super().setUp()
        db.session.add(models.User(name='Adam'))
        db.session.add(models.User(name='Bob'))
        db.session.add(models.User(name='Chuck'))
        db.session.commit()

        db.session.add(models.Loan(
            lender=models.User.query.filter_by(name='Chuck').first(),
            borrower=models.User.query.filter_by(name='Bob').first(),
            amount=3.0
        ))
        db.session.commit()

    def test_borrower_has_negative_balance(self):
        payload = {"lender": "Adam", "borrower": "Bob", "amount": 3.0}
        expected = {
            "users": [
                {"name": "Adam", "owes": {}, "owed_by": {"Bob": 3.0}, "balance": 3.0},
                {
                    "name": "Bob",
                    "owes": {"Adam": 3.0, "Chuck": 3.0},
                    "owed_by": {},
                    "balance": -6.0,
                },
            ]
        }

        response = self.app.post("/iou", data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)

    def test_lender_has_negative_balance(self):
        payload = {"lender": "Bob", "borrower": "Adam", "amount": 3.0}
        expected = {
            "users": [
                {"name": "Adam", "owes": {"Bob": 3.0}, "owed_by": {}, "balance": -3.0},
                {
                    "name": "Bob",
                    "owes": {"Chuck": 3.0},
                    "owed_by": {"Adam": 3.0},
                    "balance": 0.0,
                },
            ]
        }

        response = self.app.post("/iou", data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.data), expected)
