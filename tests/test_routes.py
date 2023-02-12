"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    def update_account_test(self):
        """Test update for an account is successful"""
        account = self._create_accounts(1)[0]

        newName = "Jake"
        newNumber = "+1(500)000-0001"

        account.name = newName
        account.phone_number = newNumber

        response = self.client.patch(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )

        newAccount = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(newAccount["name"], "Jake")
        self.assertEqual(newAccount["phone_number"], newNumber)

        # Should we double check running the read method
        # to make sure the account was actually updated here?

    def update_nonexistent_account_test(self):
        """Test for a non-existent account returns a 404"""
        account = self._create_accounts(1)[0]
        account.id = "-1"

        response = self.client.patch(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def read_account_test(self):
        """Test reading an account succeeds"""
        account = self._create_accounts(1)[0]
        id = account.id

        response = self.client.get(
            BASE_URL,
            json={"id":id},
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(account.serialize(), response.get_json())

    def read_nonexistent_account_test(self):
        """Test reading a non-existent account fails with 404"""
        id = -1
        response = self.client.get(
            BASE_URL,
            json={"id":id},
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def list_accounts_test(self):
        """Test listing accounts returns a list of the expected size"""
        expectedSize = len(Account.all())
        response = self.client.get(
            BASE_URL + "/all"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), expectedSize)

    def delete_account_test(self):
        """Test deleting account"""
        account = self._create_accounts(1)[0]
        id = account.id
        response1 = self.client.delete(
            BASE_URL,
            json={"id":id},
            content_type="application/json"
        )
        
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response1.get_json()), 0)

        # Make sure actually deleted
        response2 = self.client.get(
            BASE_URL,
            json={"id":id},
            content_type="application/json"
        )
        self.assertEqual(response2.status_code, status.HTTP_404_NOT_FOUND)