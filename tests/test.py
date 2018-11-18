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

logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

# Turn on low-level debugging
#
# rossmart.enable_lowlevel_trace()

UUID = 'ce46869c-eb06-11e8-898f-080027fe7ca7'


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
        response = self.api.lookUpRPNByEmployee('%s-0' % ppsn)
        pprint(response)

        self.assertTrue(len(response['rpns']) > 0)
        found = False
        for row in response['rpns']:
            if row['employeeID']['employeePpsn'] == test_employees[0]['ppsn']:
                found = True
                break

        self.assertTrue(found)

        # I expect this...
        # [{u'effectiveDate': u'2018-01-01',
        #             u'employeeID': {u'employeePpsn': u'7009613EA',
        #                             u'employmentID': u'0'},
        #             u'endDate': u'2018-12-31',
        #             u'exclusionOrder': False,
        #             u'incomeTaxCalculationBasis': u'CUMULATIVE',
        #             u'incomeTaxDeductedToDate': 0.0,
        #             u'lptToDeduct': 0.0,
        #             u'name': {u'familyName': u'Turner_TEST', u'firstName': u'Joan'},
        #             u'payForIncomeTaxToDate': 0.0,
        #             u'rpnIssueDate': u'2018-11-09',
        #             u'rpnNumber': u'5',
        #             u'taxRates': [{u'index': 1,
        #                            u'taxRatePercent': 20.0,
        #                            u'yearlyRateCutOff': 43550.0},
        #                           {u'index': 2, u'taxRatePercent': 40.0}],
        #             u'uscRates': [{u'index': 1,
        #                            u'uscRatePercent': 0.5,
        #                            u'yearlyUSCRateCutOff': 12012.0},
        #                           {u'index': 2,
        #                            u'uscRatePercent': 2.0,
        #                            u'yearlyUSCRateCutOff': 19372.0},
        #                           {u'index': 3,
        #                            u'uscRatePercent': 4.75,
        #                            u'yearlyUSCRateCutOff': 70044.0},
        #                           {u'index': 4,
        #                            u'uscRatePercent': 8.0,
        #                            u'yearlyUSCRateCutOff': 70044.0}],
        #             u'uscStatus': u'ORDINARY',
        #             u'yearlyTaxCredits': 4950.0}],
        #  u'taxYear': 2018,
        #  u'totalRPNCount': 1}

    def test_02_lookUpRPNByEmployer(self):
        print("\n\nRetrieve RPN for all employees")
        response = self.api.lookUpRPNByEmployer()
        pprint(response)

        self.assertTrue(len(response['rpns']) > 0)
        found = False
        for row in response['rpns']:
            if row['employeeID']['employeePpsn'] == test_employees[0]['ppsn']:
                found = True
                break

        self.assertTrue(found)

    def test_03_createTemporaryRpn(self):
        print("\n\nCreate RPN for unemployed employees")

        response = self.api.createTemporaryRpn(
            employeeID={"employeePpsn": unemployed_customer["ppsn"], "employmentID": "0"},
            name=unemployed_customer["name"],
            employmentStartDate="2018-11-01",
            # requestId=UUID
        )
        pprint(response)
        found = False
        for row in (response.get('rpns') or []):
            if row['employeeID']['employeePpsn'] == unemployed_customer['ppsn']:
                found = True
                break

        # Do we already have an entry?
        already_installed = self.api.validation_errors("4003")

        self.assertTrue(found or already_installed)

    def test_03_createTemporaryRpn2(self):
        print("\n\nDuplicate Create RPN for unemployed employees request")

        try:
            self.api.createTemporaryRpn(
                employeeID={"employeePpsn": unemployed_customer["ppsn"], "employmentID": "0"},
                name=unemployed_customer["name"],
                employmentStartDate="2018-11-01",
                requestId=UUID
            )

            # UUID was used in first test...

        except rossmart.RosSmartException as e:

            # Do we already have an entry - check for error 4001 (Duplicate)?
            duplicated = e.validation_errors("4001")
            pprint(duplicated)
            assert(duplicated)


if __name__ == '__main__':
    unittest.main()
