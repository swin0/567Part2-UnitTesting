import time
import json
import csv
import unittest
import os

# Import your functions and the test suite
from MRTD import encode_mrz, decode_mrz
from MTTDTest import TestMRTD 

def load_data():
    print("Loading JSON data...")
    with open('data/records_decoded.json', 'r') as f:
        decoded_data = json.load(f)['records_decoded']
        
    with open('data/records_encoded.json', 'r') as f:
        encoded_data = json.load(f)['records_encoded']
        
    return decoded_data, encoded_data

def format_decoded_record(record):
    flat_record = {}
    flat_record["document_type"] = "P" 
    flat_record["issuing_country"] = record["line1"].get("issuing_country", "USA")
    flat_record["name"] = f"{record['line1'].get('last_name', '')}<<{record['line1'].get('given_name', '').replace(' ', '<')}"
    flat_record["passport_number"] = record["line2"].get("passport_number", "")
    flat_record["nationality"] = record["line2"].get("country_code", "")
    flat_record["birth_date"] = record["line2"].get("birth_date", "")
    flat_record["gender"] = record["line2"].get("sex", "")
    flat_record["expiry_date"] = record["line2"].get("expiration_date", "")
    flat_record["personal_number"] = record["line2"].get("personal_number", "")
    return flat_record

def run_performance_tests():
    decoded_records, encoded_records = load_data()
    k_intervals = [100] + list(range(1000, 10001, 1000))
    results = []
    
    print("Starting performance profiling...")
    
    for k in k_intervals:
        print(f"Testing k = {k} records...")
        
        flat_records_to_encode = [format_decoded_record(r) for r in decoded_records[:k]]
        records_to_decode = encoded_records[:k]
        
        # ==========================================
        # 1. Encode Without Tests
        # ==========================================
        start_time = time.perf_counter()
        for record in flat_records_to_encode:
            try:
                encode_mrz(record)
            except ValueError:
                pass 
        encode_no_test_time = time.perf_counter() - start_time
        
        # ==========================================
        # 2. Decode Without Tests
        # ==========================================
        start_time = time.perf_counter()
        for record_str in records_to_decode:
            if ";" in record_str:
                line1, line2 = record_str.split(";")
                try:
                    decode_mrz(line1, line2)
                except ValueError:
                    pass
        decode_no_test_time = time.perf_counter() - start_time

        # ==========================================
        # 3. Unit Test Execution 
        # ==========================================
        start_time = time.perf_counter()
        suite = unittest.TestLoader().loadTestsFromTestCase(TestMRTD)
        unittest.TextTestRunner(verbosity=0).run(suite)
        unit_test_time = time.perf_counter() - start_time

        # ==========================================
        # 4. Calculate "With Test" Times
        # ==========================================
        encode_with_test_time = encode_no_test_time + unit_test_time
        decode_with_test_time = decode_no_test_time + unit_test_time

        results.append({
            "Input_Size_k": k,
            "Encode_No_Test_s": encode_no_test_time,
            "Encode_With_Test_s": encode_with_test_time,
            "Decode_No_Test_s": decode_no_test_time,
            "Decode_With_Test_s": decode_with_test_time
        })

    # ==========================================
    # Folder Creation and CSV Export
    # ==========================================
    output_folder = "performance_result"
    os.makedirs(output_folder, exist_ok=True) 
    file_path = os.path.join(output_folder, 'performance_results.csv')

    print(f"Writing results to {file_path}...")
    with open(file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Input_Size_k", "Encode_No_Test_s", "Encode_With_Test_s", "Decode_No_Test_s", "Decode_With_Test_s"])
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    run_performance_tests()