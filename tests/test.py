import unittest
import rossmart


class Tester(unittest.TestCase):

    def test_handshake(self):

        test_employerRegistrationNumber = "8000278TH"
        test_taxYear = "2018"
        password = "997ed2e8"
        public_key_path = "testset2/public_key"
        private_key_path = "testset2/private_key"

        api = rossmart.RosSmart(
            public_key_path=public_key_path,
            private_key_path=private_key_path,
            password=password,
            taxYear=test_taxYear,
            employerRegistrationNumber=test_employerRegistrationNumber)

        api.handshake()


if __name__ == '__main__':
    unittest.main()
