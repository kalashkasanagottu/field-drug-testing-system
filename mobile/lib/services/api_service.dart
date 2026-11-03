import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/test_record.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000/api'; // Android emulator localhost
  String? _token;

  void setToken(String token) {
    _token = token;
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_token != null) 'Authorization': 'Bearer $_token',
  };

  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _token = data['access_token'];
      return data;
    } else {
      throw Exception('Authentication failed');
    }
  }

  Future<List<TestKit>> fetchKits() async {
    final response = await http.get(Uri.parse('$baseUrl/kits'), headers: _headers);
    if (response.statusCode == 200) {
      final List list = jsonDecode(response.body);
      return list.map((e) => TestKit.fromJson(e)).toList();
    }
    return [];
  }

  Future<List<MobileTestRecord>> fetchTests() async {
    final response = await http.get(Uri.parse('$baseUrl/tests'), headers: _headers);
    if (response.statusCode == 200) {
      final List list = jsonDecode(response.body);
      return list.map((e) => MobileTestRecord.fromJson(e)).toList();
    }
    return [];
  }

  Future<Map<String, dynamic>> submitTestWithImage({
    required int kitId,
    required String batchNumber,
    String? caseReference,
    String? notes,
    double? latitude,
    double? longitude,
    required File imageFile,
  }) async {
    // 1. Create Test Record
    final createRes = await http.post(
      Uri.parse('$baseUrl/tests'),
      headers: _headers,
      body: jsonEncode({
        'kit_id': kitId,
        'kit_batch_number': batchNumber,
        'case_reference': caseReference,
        'notes': notes,
        'gps_latitude': latitude,
        'gps_longitude': longitude,
        'device_timestamp': DateTime.now().toUtc().toIso8601String(),
      }),
    );

    if (createRes.statusCode != 200) {
      throw Exception('Failed to initialize test record');
    }

    final testData = jsonDecode(createRes.body);
    final String testId = testData['test_id'];

    // 2. Upload Image for CV Analysis
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/tests/$testId/capture'));
    if (_token != null) request.headers['Authorization'] = 'Bearer $_token';
    request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));

    final streamedRes = await request.send();
    final res = await http.Response.fromStream(streamedRes);

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Computer vision analysis failed: ${res.body}');
    }
  }
}

final apiService = ApiService();
