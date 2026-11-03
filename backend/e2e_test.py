"""End-to-end test of the complete forensic evidence workflow."""
import urllib.request
import json
import base64
import os
import sys

BASE = 'http://127.0.0.1:8000/api'

def request(method, path, data=None, token=None):
    url = BASE + path
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body.decode('utf-8'))
        except Exception:
            return e.code, {'detail': str(e)}

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} {detail}")

# 1. Login as officer
print("=== 1. Officer Login ===")
status, data = request('POST', '/auth/login', {'username': 'officer1', 'password': 'OfficerPass123!'})
check("Login returns 200", status == 200, str(status))
check("Token returned", 'access_token' in data, str(data))
check("Role is FIELD_OFFICER", data.get('role') == 'FIELD_OFFICER', str(data.get('role')))
token = data.get('access_token')
user_id = data.get('user_id')

# 2. Login as admin
print("\n=== 2. Admin Login ===")
status, admin_data = request('POST', '/auth/login', {'username': 'admin', 'password': 'AdminPass123!'})
check("Admin login returns 200", status == 200, str(status))
admin_token = admin_data.get('access_token')

# 3. List kits
print("\n=== 3. List Test Kits ===")
status, kits = request('GET', '/kits', token=token)
check("Kits listing returns 200", status == 200, str(status))
check("At least 4 kits", len(kits) >= 4, str(len(kits)))
kit_id = kits[0]['id'] if kits else None

# 4. Create test record
print("\n=== 4. Create Test Record ===")
status, test = request('POST', '/tests', {
    'kit_id': kit_id,
    'kit_batch_number': 'LOT-E2E-001',
    'kit_expiry_date': '2027-12-31',
    'case_reference': 'CASE-E2E-001',
    'notes': 'End-to-end verification test',
    'gps_latitude': 37.7749,
    'gps_longitude': -122.4194,
    'gps_accuracy_meters': 4.2,
    'device_timestamp': '2026-11-03T07:00:00Z'
}, token=token)
check("Test creation returns 200", status == 200, str(status))
check("Test ID generated", 'test_id' in test, str(test))
test_id = test.get('test_id')

# 5. Upload image for CV analysis
print("\n=== 5. Upload Image for CV Analysis ===")
img_path = 'uploads/original/DT-20261102-C7E1_orig.jpg'
if os.path.exists(img_path):
    # Send as multipart/form-data (base64 as form field)
    url = BASE + f'/tests/{test_id}/capture'
    boundary = '----FormBoundaryE2E'
    body_parts = []
    body_parts.append('--' + boundary)
    body_parts.append('Content-Disposition: form-data; name="image_base64"')
    body_parts.append('')
    with open(img_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode()
    body_parts.append('data:image/jpeg;base64,' + img_data)
    body_parts.append('--' + boundary + '--')
    body = ('\r\n'.join(body_parts)).encode('utf-8')
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'multipart/form-data; boundary=' + boundary
    }
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            analysis = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            status = e.code
            analysis = json.loads(body.decode('utf-8'))
        except Exception:
            status = e.code
            analysis = {'detail': str(e)}
    check("Image capture returns 200", status == 200, str(status))
    check("Classification returned", 'classification_result' in analysis, str(analysis))
    check("Has disclaimer", 'disclaimer' in analysis, str(analysis))
    check("Has SHA-256 hash", 'original_image_hash' in analysis and len(analysis.get('original_image_hash', '')) == 64, str(analysis.get('original_image_hash', '')))
    check("Has digital signature", 'digital_signature' in analysis, str(analysis))
    print(f"  Classification: {analysis.get('classification_result')}")
    print(f"  SHA-256: {analysis.get('original_image_hash', '')[:16]}...")
else:
    print("  SKIP: Test image not found")

# 6. Get test detail
print("\n=== 6. Get Test Record Detail ===")
status, detail = request('GET', f'/tests/{test_id}', token=token)
check("Test detail returns 200", status == 200, str(status))
check("Has verification status", 'verification_status' in detail, str(detail))
check("Has GPS data", detail.get('gps_latitude') is not None, str(detail.get('gps_latitude')))
check("Has digital signature", detail.get('digital_signature') is not None, str(detail))

# 7. Verify evidence integrity
print("\n=== 7. Verify Evidence Integrity ===")
status, verify = request('POST', f'/evidence/{test_id}/verify', {
    'test_id': test_id,
    'check_image_tampering': True,
    'check_digital_signature': True
}, token=token)
check("Verification returns 200", status == 200, str(status))
check("Hash verified", verify.get('image_hash_verified') == True, str(verify.get('image_hash_verified')))
check("Signature verified", verify.get('signature_verified') == True, str(verify.get('signature_verified')))
check("Status is VERIFIED", verify.get('status') == 'VERIFIED', str(verify.get('status')))
print(f"  Status: {verify.get('status')}")
print(f"  Details: {verify.get('details')}")

# 8. Tamper detection
print("\n=== 8. Tamper Detection ===")
status, tamper = request('POST', f'/evidence/{test_id}/simulate-tampering', token=token)
check("Tamper simulation returns 200", status == 200, str(status))

status, verify_after = request('POST', f'/evidence/{test_id}/verify', {
    'test_id': test_id,
    'check_image_tampering': True,
    'check_digital_signature': True
}, token=token)
check("Tamper detected - hash failed", verify_after.get('image_hash_verified') == False, str(verify_after.get('image_hash_verified')))
check("Tamper detected - integrity failed", verify_after.get('status') == 'INTEGRITY_FAILED', str(verify_after.get('status')))
print(f"  After tamper status: {verify_after.get('status')}")

# Restore the tampered image
status, _ = request('POST', f'/evidence/{test_id}/simulate-tampering', token=token)  # This won't restore, but test continues

# 9. Generate PDF report
print("\n=== 9. Generate PDF Report ===")
status, report = request('POST', f'/reports/{test_id}/generate', token=token)
check("Report generation returns 200", status == 200, str(status))
check("Report file size > 0", report.get('file_size', 0) > 1000, str(report.get('file_size')))

# 10. Download PDF
print("\n=== 10. Download PDF Report ===")
req = urllib.request.Request(BASE + f'/reports/{test_id}/download', headers={'Authorization': 'Bearer ' + token})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        pdf_data = resp.read()
        check("PDF download returns 200", resp.status == 200, str(resp.status))
        check("PDF content type", resp.headers.get('content-type') == 'application/pdf', resp.headers.get('content-type'))
        check("PDF size > 1000 bytes", len(pdf_data) > 1000, str(len(pdf_data)))
except Exception as e:
    check("PDF download", False, str(e))

# 11. Test history search
print("\n=== 11. Searchable Test History ===")
status, tests = request('GET', '/tests', token=token)
check("Test history returns 200", status == 200, str(status))
check("Has test records", len(tests) > 0, str(len(tests)))
found = any(t.get('test_id') == test_id for t in tests)
check("Our test appears in history", found, "not found")

# 12. Test auth endpoints
print("\n=== 12. Auth Endpoints ===")
status, forgot = request('POST', '/auth/forgot-password', {'username': 'admin'})
check("Forgot password returns 200", status == 200, str(status))

# 13. Test dashboard stats
print("\n=== 13. Dashboard Analytics ===")
status, stats = request('GET', '/analytics/dashboard', token=admin_token)
check("Dashboard returns 200", status == 200, str(status))
check("Has total_tests", 'total_tests' in stats, str(stats))
print(f"  Total tests: {stats.get('total_tests')}")
print(f"  Positive: {stats.get('positive_count')}")
print(f"  Negative: {stats.get('negative_count')}")
print(f"  Inconclusive: {stats.get('inconclusive_count')}")
print(f"  Verified: {stats.get('verified_count')}")

print("\n=== E2E RESULTS ===")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
if failed > 0:
    sys.exit(1)
else:
    print("  ALL TESTS PASSED")
    sys.exit(0)