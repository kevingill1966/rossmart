#
#   rossmart.py
#
#   This file wraps the ROS SMART payrll API.
#
#   https://revenue-ie.github.io/paye-employers-documentation/
#
#   https://revenue-ie.github.io/paye-employers-documentation/rest/REST_Web_Service_Integration_Guide.pdf
#
#   https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html
#
import json
import uuid
import requests
try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode

import logging
try:
    from md5 import md5
except:
    from hashlib import md5
import base64
import hashlib

from requests_http_signature import HTTPSignatureHeaderAuth


def enable_lowlevel_trace(enable=True):
    """
        Turn on low-level debugging at the low-level http library.
        This gives a printout of the headers and raw requests.
    """
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client

    if enable:
        http_client.HTTPConnection.debuglevel = 1
    else:
        http_client.HTTPConnection.debuglevel = 0


TEST_ROOT = 'https://softwaretest.ros.ie/paye-employers/v1/rest'
LIVE_ROOT = 'https://ros.ie/paye-employers/v1/rest'

logger = logging.getLogger("rossmart")


class RosSmartException(Exception):
    """
        Error connecting to ROS Smart API
    """
    message = None
    status_code = None
    payload = None
    response = None
    original_exception = None

    def __init__(self, message=None, status_code=None, text=None, response=None, original_exception=None, payload=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.payload = payload
        self.text = text
        self.original_exception = original_exception

    def __str__(self):
        return self.message

    def validation_errors(self, code):
        """
            The server has number of business level errors.
            These are accessible directly so that the client can be simpler.

            I cannot find the reference for these codes at the moment.
        """
        try:
            j = self.response.json()
            validationErrors = j['validationErrors']
            return [err for err in validationErrors if err.get('code') == code]
        except Exception:
            return []


class RosSmart:
    """
    Provide a wrapper for the ROS Smart API. (Ireland Revenue Services PAYE API).

    Parameters:

        public_key_path: Path to your public key, extracted as per notes above
        private_key_path: Path to your private key, extracted as per notes above
        password: Password supplied for the key via the softwaretest.ros.ie site
        taxYear: Tax year being applied
        employerRegistrationNumber: Your employer id
        test_service: Set to false to use live URLs - not published yet.
        hashed_password: use hashed password instead of original password

    The following class attributes can be overridden in a subclass. These are passed on all
    requests to the API.

        agentTain = None
        softwareUsed = "internal"
        softwareVersion = "1"
    """

    public_key = None
    private_key = None
    hashed_password = None
    url_root = False

    # Fixed parameters to REST requests - can be customised in subclass
    agentTain = None
    softwareUsed = "internal"
    softwareVersion = "1"

    # I don't like camel-case, but I use it here for consistency with the ROS docs.
    taxYear = None
    employerRegistrationNumber = None

    # Used to make a simple API for errors
    _last_response = None

    def __init__(self,
            public_key_path=None,
            private_key_path=None,
            taxYear=None,                                  # Tax Year - 4 digit string
            hashed_password=None,                          # Hashed password
            password=None,                                 # Original Password
            employerRegistrationNumber=None,               # Employers Reference Number
            test_server=False):

        self.taxYear = taxYear
        self.employerRegistrationNumber = employerRegistrationNumber

        if test_server:
            self.url_root = TEST_ROOT
        else:
            self.url_root = LIVE_ROOT

        if hashed_password:
            self.hashed_password = hashed_password
        else:
            self.hashed_password = self.hash_password(password)

        # Cannot run  algorithm="rsa-sha256" at the moment, no valid key.
        with open(public_key_path, 'rb') as fh:
            public_key = []
            for line in fh.readlines():
                if line and not line.startswith(b'----'):
                    public_key.append(line.strip())
            self.public_key = b''.join(public_key)

        with open(private_key_path, 'rb') as fh:
            self.private_key = fh.read()

    # ---- [ API Simplifications ]-----------------------------------------------------

    def validation_errors(self, code):
        """
            The server has number of business level errors.
            These are accessible directly from the last response so that the client can be simpler.

            TODO: I cannot find the reference for these codes at the moment.
        """
        try:
            j = self._last_response.json()
            validationErrors = j['validationErrors']
            return [err for err in validationErrors if err.get('code') == code]
        except Exception:
            return []

    # ---[ Connection Test ]------------------------------------------

    def handshake(self):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#tag/PAYE-Employers-Handshake-(Connection-Test)-REST-API

            Employer's PAYE Handshake Request.
        """
        path = '/handshake'
        qs = urlencode({
            "employerRegistrationNumber": self.employerRegistrationNumber,
            "softwareUsed": self.softwareUsed,
            "softwareVersion": self.softwareVersion
        })
        return self._get(path + '?' + qs)

    # ---[ Employers Payroll REST API ]------------------------------------------

    def checkPayrollRunComplete(self, payrollRunReference):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#operation/checkPayrollRunComplete

            Request to check the current status of an Employer's PAYE Payroll Run, based on the RunReference.
        """
        path = '/payroll/%s/%s/%s' % (self.employerRegistrationNumber, self.taxYear, payrollRunReference)
        return self._get(path)

    def checkPayrollSubmissionRequest(self, payrollRunReference, submissionID):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#operation/checkPayrollSubmissionComplete

            Request to check the current status of an Employer's PAYE Payroll Submission, based on the Submission ID.
        """
        path = '/payroll/%s/%s/%s/%s' % (self.employerRegistrationNumber, self.taxYear, payrollRunReference, submissionID)
        return self._get(path)

    def createPayrollSubmission(self, payrollRunReference, submissionID, payslips, lineItemIDsToDelete=None):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#operation/createPayrollSubmission

            Employer's PAYE Payroll Submission Request.
        """
        path = '/payroll/%s/%s/%s/%s' % (self.employerRegistrationNumber, self.taxYear, payrollRunReference, submissionID)
        payload = {"payslips": payslips}
        if lineItemIDsToDelete:
            payload["lineItemIDsToDelete"] = lineItemIDsToDelete
        return self._post(path, payload)

    # ---[ Employers RPN REST API ]------------------------------------------

    def lookUpRPNByEmployee(self, employeeId):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#operation/lookUpRPNByEmployee
            Request to get an RPN by Employee ID

            employeeId:  (concatenation of PPSN and employment id)

                    Employee's PPS Number(Used to identify the employee to which the RPN relates) and
                    Employee's Employment ID e.g. {PPS_Number}-{Employment_ID}(Unique identifier for each distinct employment for an employee.
                    If the RPN is being triggered as a result of the employee setting up the employment via Jobs and Pension
                    or contacting Revenue, this field will not be populated e.g. {PPS_Number}-)
        """
        path = '/rpn/%s/%s/%s' % (self.employerRegistrationNumber, self.taxYear, employeeId)
        return self._get(path)

    def lookUpRPNByEmployer(self, dateLastUpdated=None, employeeIDs=None):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#operation/lookUpRPNByEmployer

            Request to get an RPN by Employer Registration Number. Additionally

            dateLastUpdated: string in YYYY-MM-DD format
            employeeIDs: list of (concatenation of PPSN and employment id)

                    Employee's PPS Number(Used to identify the employee to which the RPN relates) and
                    Employee's Employment ID e.g. {PPS_Number}-{Employment_ID}(Unique identifier for each distinct employment for an employee.
                    If the RPN is being triggered as a result of the employee setting up the employment via Jobs and Pension
                    or contacting Revenue, this field will not be populated e.g. {PPS_Number}-)
        """
        path = '/rpn/%s/%s' % (self.employerRegistrationNumber, self.taxYear)
        params = []
        if dateLastUpdated:
            params.append(("dateLastUpdated", dateLastUpdated))
        if employeeIDs:
            for ppsn in employeeIDs:
                params.append(("employeeIDs", ppsn))

        return self._get(path, query_params=params)

    def createTemporaryRpn(self, employeeID, name, employmentStartDate=None, requestId=None):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#operation/createTemporaryRpn

            Create new RPN.

            employeeID:          PPSN-{employment id}
            name:                name {firstName: "", familyName: ""}
            employmentStartDate: YYYY-MM-DD
        """
        path = '/rpn/%s/%s' % (self.employerRegistrationNumber, self.taxYear)
        payload = {
            "requestId": requestId or self.mk_unique_id(),
            "newEmployeeDetails": [{
                "employeeID": employeeID,
                "name": name,
            }]
        }
        if employmentStartDate:
            payload["newEmployeeDetails"][0]["employmentStartDate"] = employmentStartDate
        return self._post(path, payload)

    # ---[ PERIOD RETURN REST API ]------------------------------------------

    def lookUpPayrollReturnByPeriod(self, periodStartDate, periodEndDate):
        """
            https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.html#operation/lookUpPayrollReturnByPeriod
            Look up payroll by returns period based on a range of dates.
        """
        path = '/returns_reconciliation/%s' % (self.employerRegistrationNumber)
        params = [("periodStartDate", periodStartDate), ("periodEndDate", periodEndDate)]
        return self._get(path, query_params=params)

    # ---[ Utility Methods ]------------------------------------------

    @classmethod
    def hash_password(cls, original):
        """
            Covert plain-text password to hashed password.

            The passwords use an transform before they can be used in the HTTPSignatureHeaderAuth mechanism.

            Acording to Revenue...

                The password provided is the plain text version.

                To import to windows you would need the MD5 version in base64 encoding.

                This is described in the "Appendix A - Extracting from a .p12 File" in either the REST or SOAP integreation guides.

            From: Appendix A - Extracting from a .p12 File

            The password on the P12 is not the same as the password entered by the customer. It is in fact the
            MD5 hash of that password, followed by the Base64-encoding of the resultant bytes.

            To calculate the hashed password, follow these steps:

                1.  First get the bytes of the original password, assuming a "Latin-1" encoding. For the password
                    "Password123", these bytes are: 80 97 115 115 119 111 114 100 49 50 51(i.e. the value of
                    "P" is 80, "a" is 97, etc.).
                2.  Then get the MD5 hash of these bytes. MD5 is a standard, public algorithm. Once again, for
                    the password "Password123" these bytes work out as: 66 -9 73 -83 -25 -7 -31 -107 -65 71 95
                    55 -92 76 -81 -53.
                3.  Finally, create the new password by Base64-encoding the bytes from the previous step. For
                    example, the password, "Password123" this is "QvdJref54ZW/R183pEyvyw==".
        """
        rv = base64.encodestring(md5(original.encode('utf-8')).digest())
        if type(rv) == bytes:
            return rv.replace(b'\n', b'')
        else:
            return rv.replace('\n', '')

    def mk_unique_id(self):
        """
            Generate a unique-id. This just uses uuid.
        """
        return str(uuid.uuid1())

    # ---[ Low level GET/POST methods ]------------------------------------------

    def _auth(self, post=False):
        """
            The signing mechanism uses protocol called: "The 'Signature' HTTP Header".

            https://revenue-ie.github.io/paye-employers-documentation/rest/REST_Web_Service_Integration_Guide.pdf

            Luckily, there is a Python module for handling it.

            https://github.com/kislyuk/requests-http-signature
        """
        headers=["(request-target)", "host", "date"]
        if post:
            headers.append('digest')

        return HTTPSignatureHeaderAuth(
            algorithm="rsa-sha512",
            key=self.private_key,
            passphrase=self.hashed_password,
            key_id=self.public_key.decode('utf-8'),
            headers=headers)

    def _get(self, url, query_params=None):
        """
            Wrapper to perform HTTP GET
            query_params is a list of tupples (param, value), so that names can repeat
        """
        self._last_response = None

        url = self.url_root + url
        qs = [("softwareUsed", self.softwareUsed), ("softwareVersion", self.softwareVersion)]
        if self.agentTain:
            qs.append(("agentTain", self.agentTain))
        if query_params:
            qs = qs + query_params
        qs = urlencode(qs)
        url = url + "?" + qs

        self._last_response = resp = requests.get(url, auth=self._auth())
        if not resp.ok:
            logger.error("GET [%s] failed, status_code [%s], response [%s]" % (url, resp.status_code, resp.text))
            logger.error("GET [%s] failed, status_code [%s], response [%s]" % (url, resp.status_code, resp.text))
            raise RosSmartException(
                message="GET [%s] failed, status_code [%s]" % (url, resp.status_code),
                status_code=resp.status_code,
                text=resp.text,
                response=resp)
        else:
            logger.debug("GET [%s] ok=%s, status_code [%s], response [%s]" % (url, resp.ok, resp.status_code, resp.text))
        return resp.json()

    def _post(self, url, payload, query_params=None):
        """
            Wrapper to perform HTTP POST
            query_params is a list of tupples (param, value), so that names can repeat
        """
        self._last_response = None

        url = self.url_root + url
        qs = [("softwareUsed", self.softwareUsed), ("softwareVersion", self.softwareVersion)]
        if self.agentTain:
            qs.append(("agentTain", self.agentTain))
        if query_params:
            qs = qs + query_params
        qs = urlencode(qs)
        headers = {"Content-Type": "application/json;charset=UTF-8"}

        # The 'Digest' HTTP header is created using the POST body/payload. The payload should be
        # converted to a byte array, hashed using the SHA-512 algorithm and finally base64 encoded before
        # adding it as a HTTP header.
        data = json.dumps(payload)
        digest = hashlib.sha512(data)
        digest = base64.b64encode(digest.digest()).decode()
        headers['Digest'] = digest

        url = url + "?" + qs
        self._last_response = resp = requests.post(url, auth=self._auth(post=True), data=data, headers=headers)
        if not resp.ok:
            logger.error("POST [%s] failed, status_code [%s], response [%s], payload [%s]" % (url, resp.status_code, resp.text, payload))
            raise RosSmartException(
                message="POST [%s] failed, status_code [%s]" % (url, resp.status_code),
                status_code=resp.status_code,
                text=resp.text,
                payload=payload,
                response=resp)
        else:
            logger.debug("POST [%s] ok=%s, status_code [%s], response [%s]" % (url, resp.ok, resp.status_code, resp.text))
        return resp.json()
