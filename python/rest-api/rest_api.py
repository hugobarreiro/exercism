import json


class RestAPI:
    def __init__(self, database=None):
        self.database = database

    def _search_user(self, name):
        for user in self.database['users']:
            if user['name'] == name:
                return user
        raise ValueError('User not found.')

    def _add_user(self, name):
        self.database['users'].append(dict(
            name=name,
            owes={},
            owed_by={},
            balance=0
        ))
        self.database['users'].sort(key=lambda u: u['name'])

    def _lend(self, lender, borrower, amount):
        lender = self._search_user(lender)
        borrower = self._search_user(borrower)

        credit = lender['owed_by'].pop(borrower['name'], 0) - lender['owes'].pop(borrower['name'], 0)

        borrower['owed_by'].pop(lender['name'], 0)
        borrower['owes'].pop(lender['name'], 0)

        credit += amount

        if credit > 0:
            credit_user, debt_user = lender, borrower
        else:
            credit_user, debt_user = borrower, lender
            credit = -credit

        if credit != 0:
            credit_user['owed_by'][debt_user['name']] = credit
            debt_user['owes'][credit_user['name']] = credit

        credit_user['balance'] = sum(credit_user['owed_by'].values()) - sum(credit_user['owes'].values())
        debt_user['balance'] = sum(debt_user['owed_by'].values()) - sum(debt_user['owes'].values())

    def get(self, url, payload=None):
        if url == '/users':
            if payload is None:
                return json.dumps(self.database)
            else:
                payload = json.loads(payload)
                response = dict(users=[])
                for user in payload['users']:
                    try:
                        response['users'].append(self._search_user(user))
                    except ValueError as ex:
                        return json.dumps(dict(error=ex.message))
                response['users'].sort(key=lambda u: u['name'])
                return json.dumps(response)

    def post(self, url, payload=None):
        if url == '/add':
            payload = json.loads(payload)
            self._add_user(payload['user'])
            return json.dumps(self._search_user(payload['user']))
        elif url == '/iou':
            payload = json.loads(payload)
            self._lend(**payload)
            response = self.get(
                url='/users',
                payload=json.dumps(dict(users=[payload['lender'], payload['borrower']]))
            )
            print(response)
            return response

