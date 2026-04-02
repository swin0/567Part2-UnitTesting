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

    # ==========================================
    # Additional Test Cases for Mutation Testing
    # ==========================================

    def test_decode_mrz_invalid_type_line2(self):
        """Kills mutants altering the type check on line2."""
        with self.assertRaises(ValueError):
            MRTD.decode_mrz(self.valid_line1, 12345)

    def test_decode_mrz_invalid_length_line2(self):
        """Kills mutants altering the length check on line2."""
        with self.assertRaises(ValueError):
            MRTD.decode_mrz(self.valid_line1, "SHORTLINE")

    def test_encode_mrz_uses_default_values(self):
        """
        Kills mutants that alter the default fallback strings in encode_mrz 
        (e.g., changing 'USA' to something else) by providing a dictionary 
        that lacks the optional fields.
        """
        minimal_data = {
            "passport_number": "123456789",
            "nationality": "CAN",
            "birth_date": "900101",
            "gender": "M",
            "expiry_date": "300101"
            # Missing document_type, issuing_country, name, and personal_number
        }
        
        line1, line2 = MRTD.encode_mrz(minimal_data)
        
        # Check that the default values were actually used
        self.assertTrue(line1.startswith("P<USA"), "Default document_type 'P' and country 'USA' were not used.")
        self.assertIn("DOE<<JOHN", line1, "Default name was not used.")
        
        # Check that missing personal number is handled correctly (defaults to empty string, padded with '<')
        self.assertTrue(line2.endswith("<" * 14 + "00"), "Missing personal_number was not padded correctly.")
        
    def test_decode_mrz_length_boundaries(self):
        """Kills mutants that change the '44' length check to 43 or 45."""
        line_43 = "A" * 43
        line_45 = "A" * 45
        with self.assertRaises(ValueError):
            MRTD.decode_mrz(line_43, self.valid_line2)
        with self.assertRaises(ValueError):
            MRTD.decode_mrz(line_45, self.valid_line2)
        with self.assertRaises(ValueError):
            MRTD.decode_mrz(self.valid_line1, line_43)
        with self.assertRaises(ValueError):
            MRTD.decode_mrz(self.valid_line1, line_45)

    def test_decode_mrz_all_fields(self):
        """Kills mutants that alter the slicing indices of fields not previously asserted."""
        fields = MRTD.decode_mrz(self.valid_line1, self.valid_line2)
        
        # Asserting the fields that were previously ignored
        self.assertEqual(fields["name"], "ERIKSSON  ANNA MARIA")
        self.assertEqual(fields["raw_name"], "ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<")
        self.assertEqual(fields["nationality"], "UTO")
        self.assertEqual(fields["birth_date"], "740812")
        self.assertEqual(fields["expiry_date"], "120415")
        self.assertEqual(fields["personal_number"], "ZE184226B<<<<<")

    def test_encode_mrz_truncation(self):
        """Kills mutants that alter the [:9], [:3], etc. truncation limits."""
        long_data = {
            "document_type": "P",
            "issuing_country": "UTOOO", # Too long, should be 3
            "name": "A" * 50, # Too long, should be truncated to fit 39
            "passport_number": "1234567890", # 10 chars, should be 9
            "nationality": "UTOO", # 4 chars, should be 3
            "birth_date": "7408123", # 7 chars, should be 6
            "gender": "FM", # 2 chars, should be 1
            "expiry_date": "1204156", # 7 chars, should be 6
            "personal_number": "123456789012345" # 15 chars, should be 14
        }
        line1, line2 = MRTD.encode_mrz(long_data)
        
        # Verify truncation happened at the exact right characters
        self.assertEqual(line1[2:5], "UTO") 
        self.assertEqual(line2[0:9], "123456789") 
        self.assertEqual(line2[10:13], "UTO") 
        self.assertEqual(line2[13:19], "740812") 
        self.assertEqual(line2[20], "F") 
        self.assertEqual(line2[21:27], "120415") 
        self.assertEqual(line2[28:42], "12345678901234") 

    def test_validation_mismatch_other_fields(self):
        """Kills mutants that delete the check_field function calls for birth, expiry, and personal numbers."""
        fields = MRTD.decode_mrz(self.valid_line1, self.valid_line2)
        
        # Corrupt the other check digits
        fields["birth_check"] = "9" if fields["birth_check"] == "0" else "0"
        fields["expiry_check"] = "9" if fields["expiry_check"] == "0" else "0"
        fields["personal_number_check"] = "9" if fields["personal_number_check"] == "0" else "0"
        
        validation = MRTD.validate_check_digits(fields)
        self.assertFalse(validation["success"])
        
        mismatched_fields = [m["field_name"] for m in validation["mismatches"]]
        self.assertIn("birth_date", mismatched_fields)
        self.assertIn("expiry_date", mismatched_fields)
        self.assertIn("personal_number", mismatched_fields)
        
    def test_scan_mrz_stub_direct(self):
        """Kills CRP mutants hiding in the un-mocked scan_mrz stub."""
        result = MRTD.scan_mrz("raw_text")
        self.assertEqual(result, ["", ""])

    def test_fetch_data_from_db_stub_direct(self):
        """Kills mutants hiding in the database stub."""
        self.assertIsNone(MRTD.fetch_data_from_db())
        
if __name__ == '__main__':
    unittest.main()