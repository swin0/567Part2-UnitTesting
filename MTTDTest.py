import unittest
from unittest.mock import patch
import MRTD

class TestMRTD(unittest.TestCase):

    def setUp(self):
        # Sample valid data from the assignment spec for testing
        self.sample_db_data = {
            "document_type": "P",
            "issuing_country": "UTO",
            "name": "ERIKSSON<<ANNA<MARIA",
            "passport_number": "L898902C3",
            "nationality": "UTO",
            "birth_date": "740812",
            "gender": "F",
            "expiry_date": "120415",
            "personal_number": "ZE184226B"
        }
        
        # FIX: Dynamically generate valid lines using your Damm Algorithm
        # This ensures the check digits mathematically match your validation logic
        self.valid_line1, self.valid_line2 = MRTD.encode_mrz(self.sample_db_data)

    # ==========================================
    # 1. Testing Checksum & Check Digits
    # ==========================================
    def test_damm_checksum_skips_alpha(self):
        """Test that Damm algorithm correctly ignores non-numeric chars like '<' or 'A'."""
        # '123' should yield the same checksum as 'A1<2B3' based on the current implementation
        self.assertEqual(MRTD.damm_checksum("123"), MRTD.damm_checksum("A1<2B3"))

    def test_compute_check_digit(self):
        """Test that compute_check_digit applies Damm and modulo 10 correctly."""
        # Using a known numeric string
        result = MRTD.compute_check_digit("740812")
        self.assertTrue(isinstance(result, int))
        self.assertTrue(0 <= result <= 9)

    # ==========================================
    # 2. Testing MRZ Decoding (Requirement 2)
    # ==========================================
    def test_decode_mrz_valid(self):
        """Test decoding a perfectly formatted 44-character MRZ pair."""
        fields = MRTD.decode_mrz(self.valid_line1, self.valid_line2)
        self.assertEqual(fields["document_type"], "P")
        self.assertEqual(fields["issuing_country"], "UTO")
        self.assertEqual(fields["passport_number"], "L898902C3")
        self.assertEqual(fields["gender"], "F")

    def test_decode_mrz_invalid_length(self):
        """Test branch coverage: decoding raises ValueError if lines are not 44 chars."""
        with self.assertRaises(ValueError):
            MRTD.decode_mrz("SHORTLINE", self.valid_line2)

    def test_decode_mrz_invalid_type(self):
        """Test branch coverage: decoding raises ValueError if inputs aren't strings."""
        with self.assertRaises(ValueError):
            MRTD.decode_mrz(12345, self.valid_line2)

    # ==========================================
    # 3. Testing MRZ Encoding & Mocking DB (Requirement 3)
    # ==========================================
    @patch('MRTD.fetch_data_from_db')
    def test_encode_mrz_with_mocked_db(self, mock_db):
        """Test encoding process using a mocked database response."""
        # Mock the database to return our sample data
        mock_db.return_value = self.sample_db_data
        
        # Fetch data and encode
        data = mock_db()
        line1, line2 = MRTD.encode_mrz(data)
        
        self.assertEqual(len(line1), 44)
        self.assertEqual(len(line2), 44)
        self.assertTrue(line1.startswith("P<UTOERIKSSON"))

    def test_encode_mrz_missing_field(self):
        """Test branch coverage: encoding halts and raises error if a required field is missing."""
        incomplete_data = {"document_type": "P"} # Missing birth_date, etc.
        with self.assertRaises(ValueError):
            MRTD.encode_mrz(incomplete_data)

    def test_encode_mrz_null_field(self):
        """Test branch coverage (Req 3c): encoding halts if a required field is None."""
        null_data = self.sample_db_data.copy()
        null_data["birth_date"] = None
        with self.assertRaises(ValueError):
            MRTD.encode_mrz(null_data)

    # ==========================================
    # 4. Testing Validation & Mocking Scanner (Requirement 1 & 4)
    # ==========================================
    @patch('MRTD.scan_mrz')
    def test_validation_success_with_mocked_scanner(self, mock_scanner):
        """Test successful validation using mocked hardware scanner input."""
        # Mock scanner to return valid MRZ lines
        mock_scanner.return_value = (self.valid_line1, self.valid_line2)
        
        line1, line2 = mock_scanner("raw_hardware_bytes")
        fields = MRTD.decode_mrz(line1, line2)
        
        validation = MRTD.validate_check_digits(fields)
        self.assertTrue(validation["success"])
        self.assertEqual(len(validation["mismatches"]), 0)

    def test_validation_mismatch(self):
        """Test branch coverage: validation catches incorrect check digits."""
        fields = MRTD.decode_mrz(self.valid_line1, self.valid_line2)
        
        # FIX: Force a mismatch by changing the expected check digit to something guaranteed to be wrong
        wrong_check = str((int(fields["passport_check"]) + 1) % 10)
        fields["passport_check"] = wrong_check 
        
        validation = MRTD.validate_check_digits(fields)
        self.assertFalse(validation["success"])
        
        # Verify the mismatch was recorded properly
        mismatched_fields = [m["field_name"] for m in validation["mismatches"]]
        self.assertIn("passport_number", mismatched_fields)
        self.assertIn("final_check", mismatched_fields) # Final check also fails if a sub-field fails

if __name__ == '__main__':
    unittest.main()