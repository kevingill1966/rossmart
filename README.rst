ROS SMART
=========

ROS is the Revenue Online System in Ireland. A new API has been developed for 2019.
This module provides a low level Python wrapper for the API.

References
----------

    https://revenue-ie.github.io/paye-employers-documentation/

    https://revenue-ie.github.io/paye-employers-documentation/rest/paye-employers-rest-api.json

Retrieve your certificate.
--------------------------

This code has only been tested against the test environment. 

You need an account in the ROS Public Interface Test (PIT) environment.

Login to the PIT. It gives a list of test employers. These are mine as an example::

    https://softwaretest.ros.ie/paye-employers-self-service/dashboard

    Employer: 8000278TH
    Password: 997ed2e8
    Employee Details: [ { "firstName" : "Joan", "surName" : "Turner_TEST", "ppsn" : "7009613EA" } ]
    Cert: 999963889.p12

You will need a hashed password to extract your certificate.::

    python
    import rossmart
    >>> rossmart.RosSmart.hash_password('997ed2e8')
    'LZsLV0mNAdVwWI7ZyJ0Z5A=='

I used openssl on Linux to extract the p12 file to a PUBLIC KEY file.::

    openssl pkcs12 -in 999963889.p12 -out temp_file -clcerts -nokeys
    Enter Import Password: LZsLV0mNAdVwWI7ZyJ0Z5A==

    openssl x509 -in temp_file  > public_key
    rm temp_file

I extracted the ENCRYPTED PRIVATE KEY as follows::

    openssl pkcs12 -in 999963889.p12 -nocerts  -out private_key
    Enter Import Password: LZsLV0mNAdVwWI7ZyJ0Z5A==
    Enter PEM pass phrase: LZsLV0mNAdVwWI7ZyJ0Z5A==
    Verifying - Enter PEM pass phrase: LZsLV0mNAdVwWI7ZyJ0Z5A==

Verify your keys
----------------

This "handshaking" code will verify your keys have been extracted 
correctly and will work.::

    import rossmart

    test_employerRegistrationNumber = "8000278TH"
    test_taxYear = "2018"
    password = "997ed2e8"
    public_key_path = "testset2/public_key"
    private_key_path = "testset2/private_key"

    rossmart = RosSmart(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
        password=password,
        taxYear=test_taxYear,
        employerRegistrationNumber=test_employerRegistrationNumber)

    rossmart.handshake()

API Documentation
-----------------

Use the python interpreter to list the API documentation in docstrings::

    python
    >>> import rossmart
    >>> help(rossmart.RosSmart)

See the test folder for a unit-test script.

Troubleshooting
---------------

The software uses the requests library. Turn on low-level debugging::

    import http.client as http_client
    http_client.HTTPConnection.debuglevel = 1
