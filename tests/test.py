import logging
import unittest
import rossmart
from pprint import pprint
import uuid
import time

# Configuration downloaded for my account. See README in testset2
# unfortunately, the data gets wiped. Setting it up is non-trivial.
test_employees = [{"firstName": "Joan", "surName": "Turner_TEST", "ppsn": "7009613EA"}]
test_employerRegistrationNumber = "8000278TH"
test_taxYear = "2019"
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
RUNUUID = str(uuid.uuid1())


class Tester(unittest.TestCase):

    rpns = []

    def setUp(self):
        self.api = rossmart.RosSmart(
            public_key_path=public_key_path,
            private_key_path=private_key_path,
            password=password,
            taxYear=test_taxYear,
            test_server=True,
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

        self.__class__.rpns = response['rpns']

    def test_03_createTemporaryRpn(self):
        print("\n\nCreate RPN for unemployed employees")

        response = self.api.createTemporaryRpn(
            employeeID={"employeePpsn": unemployed_customer["ppsn"], "employmentID": "0"},
            name=unemployed_customer["name"],
            employmentStartDate="2019-01-01",
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
                employmentStartDate="2019-01-01",
                requestId=UUID
            )

            # UUID was used in first test...

        except rossmart.RosSmartException as e:

            # Do we already have an entry - check for error 4001 (Duplicate)?
            duplicated = e.validation_errors("4001")
            pprint(duplicated)
            assert(duplicated)

    def test_04_createSubmission(self):
        print("\n\nCreating payroll submission")

        rpn = None
        for r in self.__class__.rpns:
            if r["employeeID"]["employeePpsn"] == test_employees[0]['ppsn']:
                rpn = r
                break

        self.assertTrue(rpn is not None)

        # Compute taxes based on RPN
        payDate = '2019-01-01'
        grossPay = 1000.00
        payForIncomeTax = 1000.00
        incomeTaxPaid = 0                   # Total amount for employment
        payForEmployeePRSI = 1000.00
        payForEmployerPRSI = 1000.00

        # prsiExempt = False
        # prsiExemptionReason = "UNDER_16"
        prsiClassDetails = [
            {"prsiClass": "A1", "insurableWeeks": 1}
        ]

        employeePRSIPaid = 0.00
        employerPRSIPaid = 0.00
        payForUSC = 1000.00
        uscStatus = rpn["uscStatus"]
        uscPaid = 0

        # If unknown PPSN need extra fields
        # If no RPN extra fields (emergency tax)

        row = {
            "lineItemID": RUNUUID,
            "employeeID": rpn['employeeID'],
            "employerReference": "Y11111",
            "name": rpn["name"],
            "payFrequency": "WEEKLY",
            "numberOfPayPeriods": 52,
            "rpnNumber": rpn["rpnNumber"],

            "payDate": payDate,
            "grossPay": grossPay,
            "payForIncomeTax": payForIncomeTax,
            "incomeTaxPaid": incomeTaxPaid,
            "payForEmployeePRSI": payForEmployeePRSI,
            "payForEmployerPRSI": payForEmployerPRSI,
            "prsiClassDetails": prsiClassDetails,
            "employerPRSIPaid": employerPRSIPaid,
            "employeePRSIPaid": employeePRSIPaid,
            "payForUSC": payForUSC,
            "uscStatus": uscStatus,
            "uscPaid": uscPaid,
        }

        payslips = [row]

        try:
            self.api.createPayrollSubmission(payrollRunReference='2019-01-01', submissionID=RUNUUID, payslips=payslips)
        except Exception as e:
            print("Exception: createPayrollSubmission, %s" % e)

        print("Checking submission status")
        for i in range(10):
            time.sleep(1)
            self.api.checkPayrollSubmissionRequest(payrollRunReference='2019-01-01', submissionID=RUNUUID)

        print("Checking payroll status")
        self.api.checkPayrollRunComplete(payrollRunReference='2019-01-01')


if __name__ == '__main__':
    unittest.main()
