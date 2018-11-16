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


class Tester(unittest.TestCase):

    def setUp(self):
        self.api = rossmart.RosSmart(
            public_key_path=public_key_path,
            private_key_path=private_key_path,
            password=password,
            taxYear=test_taxYear,
            employerRegistrationNumber=test_employerRegistrationNumber)

    def test_handshake(self):
        print("\n\nHandshaking to verify the connection")
        self.api.handshake()

    def test_lookUpRPNByEmployee(self):
        print("\n\nRetrieve RPN for demo employee")
        ppsn = test_employees[0]["ppsn"]
        pprint(self.api.lookUpRPNByEmployee('%s-0' % ppsn))

    def test_lookUpRPNByEmployer(self):
        print("\n\nRetrieve RPN for all employees")
        pprint(self.api.lookUpRPNByEmployer())


if __name__ == '__main__':
    unittest.main()
