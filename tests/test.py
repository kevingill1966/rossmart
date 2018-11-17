import logging
import unittest
import rossmart
from pprint import pprint

# Configuration downloaded for my account. See README in testset2
# unfortunately, the data gets wiped. Setting it up is non-trivial.
test_employees = [{"firstName": "Joan", "surName": "Turner_TEST", "ppsn": "7009613EA"}]
test_employerRegistrationNumber = "8000278TH"
test_taxYear = "2018"
password = "997ed2e8"
public_key_path = "testset2/public_key"
private_key_path = "testset2/private_key"

# You have to create these in the web user interface
unemployed_customer = {
    "name": {"firstName": "Bins", "familyName": "Brent"},
    "ppsn": "7064924JA"}

logging.basicConfig(
    level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

# Turn on low-level debugging
#
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client

http_client.HTTPConnection.debuglevel = 1


class Tester(unittest.TestCase):

    def setUp(self):
        self.api = rossmart.RosSmart(
            public_key_path=public_key_path,
            private_key_path=private_key_path,
            password=password,
            taxYear=test_taxYear,
            employerRegistrationNumber=test_employerRegistrationNumber)

    def test_00_handshake(self):
        print("\n\nHandshaking to verify the connection")
        self.api.handshake()

    def test_01_lookUpRPNByEmployee(self):
        print("\n\nRetrieve RPN for demo employee")
        ppsn = test_employees[0]["ppsn"]
        pprint(self.api.lookUpRPNByEmployee('%s-0' % ppsn))

    def test_02_lookUpRPNByEmployer(self):
        print("\n\nRetrieve RPN for all employees")
        pprint(self.api.lookUpRPNByEmployer())

    def test_03_createTemporaryRpn(self):
        print("\n\nCreate RPN for unemployed employees")
        pprint(self.api.createTemporaryRpn(
            employeeID={"employeePpsn": unemployed_customer["ppsn"], "employmentID": "0"},
            name=unemployed_customer["name"],
            employmentStartDate="2018-11-01",
        ))


if __name__ == '__main__':
    unittest.main()
