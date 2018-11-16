Test Set 2
==========

This is the data for testing that I got from revenue. ::

    https://softwaretest.ros.ie/paye-employers-self-service/dashboard

    Employer: 8000278TH
    Password: 997ed2e8
    Employee Details: [ { "firstName" : "Joan", "surName" : "Turner_TEST", "ppsn" : "7009613EA" } ]
    Cert: 999963889.p12


I used the mk_password.py script to generate a hashed password::

    python mk_p12_password.py 997ed2e8
    LZsLV0mNAdVwWI7ZyJ0Z5A==

I used openssl to extract the p12 file to a PUBLIC KEY file.::

    openssl pkcs12 -in 999963889.p12 -out temp_file -clcerts -nokeys
    Enter Import Password: LZsLV0mNAdVwWI7ZyJ0Z5A==

    openssl x509 -in temp_file  > public_key
    rm temp_file

I extracted the ENCRYPTED PRIVATE KEY as follows::

    openssl pkcs12 -in 999963889.p12 -nocerts  -out private_key
    Enter Import Password: LZsLV0mNAdVwWI7ZyJ0Z5A==
    Enter PEM pass phrase: LZsLV0mNAdVwWI7ZyJ0Z5A==
    Verifying - Enter PEM pass phrase: LZsLV0mNAdVwWI7ZyJ0Z5A==
