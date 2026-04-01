"""
MRTD.py

Software functions for a Machine-Readable Travel Document (MRTD) system.

Implements:
- MRZ scanning (stub)
- MRZ decoding
- MRZ encoding
- Check digit validation using the Damm Algorithm

Vincent Sun, Billy Ye, Sydney Winstead
"""

# Damm Algorithm

DAMM_TABLE = [
    [0, 3, 1, 7, 5, 9, 8, 6, 4, 2],
    [7, 0, 9, 2, 1, 5, 4, 8, 6, 3],
    [4, 2, 0, 6, 8, 7, 1, 3, 5, 9],
    [1, 7, 5, 0, 9, 8, 3, 4, 2, 6],
    [6, 1, 2, 3, 0, 4, 5, 9, 7, 8],
    [3, 6, 7, 4, 2, 0, 9, 5, 8, 1],
    [5, 8, 6, 9, 7, 2, 0, 1, 3, 4],
    [8, 9, 4, 5, 3, 6, 2, 0, 1, 7],
    [9, 4, 3, 8, 6, 1, 7, 2, 0, 5],
    [2, 5, 8, 1, 4, 3, 6, 7, 9, 0]
]


def damm_checksum(number_str):
    """
    Computes checksum using the Damm algorithm.

    Args:
        number_str (str): numeric string

    Returns:
        int: checksum value
    """
    interim = 0
    for digit in number_str:
        if not digit.isdigit():
            continue  # Skip non-numeric characters such as '<'
        interim = DAMM_TABLE[interim][int(digit)]
    return interim


def compute_check_digit(number_str):
    """
    Computes final check digit.

    Steps:
    1. Apply Damm checksum
    2. Modulus 10

    Args:
        number_str (str): numeric string

    Returns:
        int: check digit
    """
    checksum = damm_checksum(number_str)
    return checksum % 10


# Requirement 1

def scan_mrz(raw_text):
    """
    Simulates scanning MRZ from a hardware device.
    Requirement 1a: Accept raw text output directly from hardware scanner.
    Requirement 1b: Return processed MRZ as an array of two strings.
    """
    # Hardware not implemented yet
    return ["", ""]


# Requirement 2

def decode_mrz(line1, line2):
    """
    Decodes MRZ lines into structured fields.

    Args:
        line1 (str)
        line2 (str)

    Returns:
        dict: parsed fields
    """
    if not isinstance(line1, str) or not isinstance(line2, str):
        raise ValueError("MRZ lines must be strings")

    if len(line1) != 44 or len(line2) != 44:
        raise ValueError("Invalid MRZ format: each line must be exactly 44 characters")

    fields = {}

    fields["document_type"] = line1[0]
    fields["issuing_country"] = line1[2:5]
    fields["raw_name"] = line1[5:44]
    fields["name"] = line1[5:44].replace("<", " ").strip()

    fields["passport_number"] = line2[0:9]
    fields["passport_check"] = line2[9]

    fields["nationality"] = line2[10:13]

    fields["birth_date"] = line2[13:19]
    fields["birth_check"] = line2[19]

    fields["gender"] = line2[20]

    fields["expiry_date"] = line2[21:27]
    fields["expiry_check"] = line2[27]

    fields["personal_number"] = line2[28:42]
    fields["personal_number_check"] = line2[42]
    fields["final_check"] = line2[43]

    return fields


# Requirement 3

def fetch_data_from_db():
    """
    Stub for database interaction.

    Returns:
        dict: simulated data
    """
    # Database not implemented yet
    pass


def encode_mrz(data):
    """
    Encodes fields into MRZ format.

    Args:
        data (dict)

    Returns:
        tuple: (line1, line2)
    """
    required_fields = [
        "passport_number",
        "nationality",
        "birth_date",
        "gender",
        "expiry_date"
    ]

    for field in required_fields:
            # Added 'is None' check to satisfy Requirement 3c
            if field not in data or data[field] is None:
                raise ValueError(f"Missing or null required field: {field}")

    line1 = (
        data.get("document_type", "P") +
        "<" +
        data.get("issuing_country", "USA") +
        data.get("name", "DOE<<JOHN")
    ).ljust(44, "<")[:44]

    passport_number = str(data["passport_number"]).ljust(9, "<")[:9]
    nationality = str(data["nationality"]).ljust(3, "<")[:3]
    birth_date = str(data["birth_date"]).ljust(6, "<")[:6]
    gender = str(data["gender"])[:1]
    expiry_date = str(data["expiry_date"]).ljust(6, "<")[:6]
    personal_number = str(data.get("personal_number", "")).ljust(14, "<")[:14]

    passport_cd = str(compute_check_digit(passport_number))
    birth_cd = str(compute_check_digit(birth_date))
    expiry_cd = str(compute_check_digit(expiry_date))
    personal_number_cd = str(compute_check_digit(personal_number))

    composite_data = (
        passport_number +
        passport_cd +
        birth_date +
        birth_cd +
        expiry_date +
        expiry_cd +
        personal_number +
        personal_number_cd
    )
    final_cd = str(compute_check_digit(composite_data))

    line2 = (
        passport_number +
        passport_cd +
        nationality +
        birth_date +
        birth_cd +
        gender +
        expiry_date +
        expiry_cd +
        personal_number +
        personal_number_cd +
        final_cd
    )

    return line1, line2


# Requirement 4

def validate_check_digits(fields):
    """
    Validates check digits and reports mismatches according to Requirement 4.

    Returns:
        dict: A structured validation result with success status and detailed mismatches.
    """
    validation_result = {
        "success": True,
        "mismatches": []
    }

    def check_field(field_name, original_value, extracted_check_digit):
        expected_check = str(compute_check_digit(original_value))
        if expected_check != extracted_check_digit:
            validation_result["success"] = False
            validation_result["mismatches"].append({
                "field_name": field_name,
                "original_value": original_value,
                "expected_check_digit": expected_check,
                "computed_check_digit": extracted_check_digit
            })

    check_field("passport_number", fields["passport_number"], fields["passport_check"])
    check_field("birth_date", fields["birth_date"], fields["birth_check"])
    check_field("expiry_date", fields["expiry_date"], fields["expiry_check"])
    check_field("personal_number", fields["personal_number"], fields["personal_number_check"])

    # Requirement 4 composite check
    composite_data = (
        fields["passport_number"] + fields["passport_check"] +
        fields["birth_date"] + fields["birth_check"] +
        fields["expiry_date"] + fields["expiry_check"] +
        fields["personal_number"] + fields["personal_number_check"]
    )
    
    check_field("final_check", composite_data, fields["final_check"])

    return validation_result

# Optional main

if __name__ == "__main__":
    sample_data = {
        "document_type": "P",
        "issuing_country": "USA",
        "name": "DOE<<JOHN",
        "passport_number": "123456789",
        "nationality": "USA",
        "birth_date": "900101",
        "gender": "M",
        "expiry_date": "300101",
        "personal_number": "12345678901234"
    }

    line1, line2 = encode_mrz(sample_data)
    print("Line1:", line1)
    print("Line2:", line2)

    decoded = decode_mrz(line1, line2)
    print("Decoded:", decoded)

    mismatches = validate_check_digits(decoded)
    print("Mismatches:", mismatches)