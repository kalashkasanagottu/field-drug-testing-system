class TestKit {
  final int id;
  final String name;
  final String manufacturer;
  final String analyte;
  final String instructions;

  TestKit({
    required this.id,
    required this.name,
    required this.manufacturer,
    required this.analyte,
    required this.instructions,
  });

  factory TestKit.fromJson(Map<String, dynamic> json) {
    return TestKit(
      id: json['id'],
      name: json['name'],
      manufacturer: json['manufacturer'],
      analyte: json['analyte'],
      instructions: json['instructions'] ?? '',
    );
  }
}

class MobileTestRecord {
  final String testId;
  final String? caseReference;
  final String kitName;
  final String kitBatchNumber;
  final String classificationResult;
  final String? analyteDetected;
  final String? originalImageHash;
  final String? digitalSignature;
  final double? latitude;
  final double? longitude;
  final String timestamp;
  final String syncStatus;

  MobileTestRecord({
    required this.testId,
    this.caseReference,
    required this.kitName,
    required this.kitBatchNumber,
    required this.classificationResult,
    this.analyteDetected,
    this.originalImageHash,
    this.digitalSignature,
    this.latitude,
    this.longitude,
    required this.timestamp,
    required this.syncStatus,
  });

  factory MobileTestRecord.fromJson(Map<String, dynamic> json) {
    return MobileTestRecord(
      testId: json['test_id'],
      caseReference: json['case_reference'],
      kitName: json['kit_name'] ?? 'Test Kit',
      kitBatchNumber: json['kit_batch_number'] ?? '',
      classificationResult: json['classification_result'] ?? 'UNABLE_TO_CLASSIFY',
      analyteDetected: json['analyte_detected'],
      originalImageHash: json['original_image_hash'],
      digitalSignature: json['digital_signature'],
      latitude: json['gps_latitude']?.toDouble(),
      longitude: json['gps_longitude']?.toDouble(),
      timestamp: json['created_at'] ?? '',
      syncStatus: json['sync_status'] ?? 'SYNCHRONIZED',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'test_id': testId,
      'case_reference': caseReference,
      'kit_name': kitName,
      'kit_batch_number': kitBatchNumber,
      'classification_result': classificationResult,
      'analyte_detected': analyteDetected,
      'original_image_hash': originalImageHash,
      'digital_signature': digitalSignature,
      'latitude': latitude,
      'longitude': longitude,
      'timestamp': timestamp,
      'sync_status': syncStatus,
    };
  }
}
