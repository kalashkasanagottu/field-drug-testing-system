import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import '../models/test_record.dart';
import '../services/api_service.dart';

enum _CaptureMode { camera, upload }

class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key});

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen>
    with WidgetsBindingObserver {
  List<TestKit> _kits = [];
  TestKit? _selectedKit;
  final _caseController = TextEditingController();
  final _batchController = TextEditingController(text: 'LOT-2026-MOB-101');

  bool _isLoadingKits = true;
  bool _isAnalyzing = false;
  bool _hasCameraPermission = false;
  CameraController? _cameraController;
  List<CameraDescription>? _cameras;
  XFile? _pickedFile;
  String? _imageFormatLabel;
  Map<String, dynamic>? _analysisResult;

  _CaptureMode _captureMode = _CaptureMode.camera;

  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadKits();
    _initializeCamera();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }
    if (state == AppLifecycleState.inactive) {
      _cameraController?.dispose();
    } else if (state == AppLifecycleState.resumed) {
      if (_cameraController != null && _cameraController!.value.isInitialized) {
        _initializeCamera();
      }
    }
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (!mounted) return;
      setState(() => _cameras = cameras);

      final rearCamera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.rear,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        rearCamera,
        ResolutionPreset.max,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await _cameraController!.initialize();
      if (!mounted) return;
      setState(() {
        _hasCameraPermission = true;
      });
    } on CameraException catch (e) {
      debugPrint('Camera error: $e');
      if (!mounted) return;
      setState(() {
        _hasCameraPermission = false;
      });
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    _caseController.dispose();
    _batchController.dispose();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Future<void> _loadKits() async {
    try {
      final kits = await apiService.fetchKits();
      if (!mounted) return;
      setState(() {
        _kits = kits;
        if (kits.isNotEmpty) _selectedKit = kits.first;
      });
    } finally {
      if (!mounted) return;
      setState(() => _isLoadingKits = false);
    }
  }

  Future<void> _captureFromCamera() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    try {
      final XFile photo = await _cameraController!.takePicture();
      if (!mounted) return;
      setState(() {
        _pickedFile = photo;
        _imageFormatLabel = _formatFromPath(photo.path);
        _analysisResult = null;
      });
    } on CameraException catch (e) {
      debugPrint('Capture error: $e');
    }
  }

  Future<void> _uploadFromGallery() async {
    final XFile? file = await _picker.pickImage(source: ImageSource.gallery);
    if (file != null) {
      setState(() {
        _pickedFile = file;
        _imageFormatLabel = _formatFromPath(file.path);
        _analysisResult = null;
      });
    }
  }

  String _formatFromPath(String path) {
    final ext = path.split('.').last.toUpperCase();
    return ext.isEmpty ? 'IMG' : ext;
  }

  Future<void> _analyzeImage() async {
    if (_selectedKit == null || _pickedFile == null) return;

    setState(() => _isAnalyzing = true);

    try {
      // Get device location first (GPS)
      // GPS is handled by the test creation flow; we pass what we have

      // 1. Create test record on backend
      final createRes = await apiService.submitTestWithImage(
        kitId: _selectedKit!.id,
        batchNumber: _batchController.text,
        caseReference: _caseController.text.isEmpty ? null : _caseController.text,
        imageFile: File(_pickedFile!.path),
      );

      if (!mounted) return;
      setState(() {
        _analysisResult = createRes;
        _isAnalyzing = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isAnalyzing = false;
        _analysisResult = {
          'test_id': 'DT-LOCAL-ERROR',
          'classification_result': 'UNABLE_TO_CLASSIFY',
          'analyte_detected': null,
          'classification_confidence': 0.0,
          'classification_reason': 'Analysis failed: $e',
          'source': 'Camera Capture',
          'disclaimer':
              'Automated output is a presumptive field-test result. It is not a '
              'laboratory-confirmed identification. Confirmatory laboratory '
              'testing is required.',
        };
      });
    }
  }

  void _reset() {
    setState(() {
      _pickedFile = null;
      _imageFormatLabel = null;
      _analysisResult = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Field Capture & CV Calibration',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
      ),
      body: _isLoadingKits
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_analysisResult == null) ...[
                    _buildKitDropdown(),
                    const SizedBox(height: 14),
                    _buildTextField(_caseController, 'Case File Reference',
                        Icons.folder_outlined),
                    const SizedBox(height: 14),
                    _buildTextField(_batchController, 'Kit Batch / Lot Number',
                        Icons.qr_code_2_outlined),
                    const SizedBox(height: 20),
                    _buildModeToggle(),
                    const SizedBox(height: 16),
                    _buildCameraViewport(),
                    const SizedBox(height: 20),
                    _buildActionButtons(),
                  ] else ...[
                    _buildResultCard(),
                    const SizedBox(height: 20),
                    ElevatedButton.icon(
                      onPressed: () => Navigator.of(context).pop(),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF111827),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      icon: const Icon(Icons.arrow_back_ios_new, size: 16),
                      label: const Text('Return to Dashboard'),
                    ),
                    const SizedBox(height: 10),
                    OutlinedButton.icon(
                      onPressed: _reset,
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Color(0xFF2563EB)),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      icon: const Icon(Icons.replay,
                          size: 16, color: Color(0xFF2563EB)),
                      label: const Text('New Capture',
                          style: TextStyle(color: Color(0xFF2563EB))),
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildKitDropdown() {
    return DropdownButtonFormField<TestKit>(
      value: _selectedKit,
      decoration: InputDecoration(
        labelText: 'Select Test Kit',
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        prefixIcon: const Icon(Icons.science_outlined),
      ),
      items: _kits
          .map((k) => DropdownMenuItem(
                value: k,
                child: Text(k.name, overflow: TextOverflow.ellipsis),
              ))
          .toList(),
      onChanged: (val) => setState(() => _selectedKit = val),
    );
  }

  Widget _buildTextField(
      TextEditingController ctrl, String label, IconData icon) {
    return TextField(
      controller: ctrl,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        prefixIcon: Icon(icon),
      ),
    );
  }

  Widget _buildModeToggle() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1F2937),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white12),
      ),
      padding: const EdgeInsets.all(4),
      child: Row(
        children: [
          _modeTab(_CaptureMode.camera, Icons.camera_alt_outlined, 'Camera'),
          _modeTab(
              _CaptureMode.upload, Icons.upload_file_outlined, 'Upload Image'),
        ],
      ),
    );
  }

  Widget _modeTab(_CaptureMode mode, IconData icon, String label) {
    final bool active = _captureMode == mode;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() {
          _captureMode = mode;
          _pickedFile = null;
          _imageFormatLabel = null;
        }),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: active ? const Color(0xFF2563EB) : Colors.transparent,
            borderRadius: BorderRadius.circular(9),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon,
                  size: 18,
                  color: active ? Colors.white : Colors.white54),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: active ? Colors.white : Colors.white54,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCameraViewport() {
    return Container(
      height: 320,
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: _pickedFile != null
              ? const Color(0xFF2563EB)
              : Colors.white12,
          width: _pickedFile != null ? 2 : 1,
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: _pickedFile != null
          ? _buildImagePreview()
          : _captureMode == _CaptureMode.camera
              ? _buildCameraLivePreview()
              : _buildUploadPlaceholder(),
    );
  }

  Widget _buildCameraLivePreview() {
    if (!_hasCameraPermission || _cameraController == null ||
        !_cameraController!.value.isInitialized) {
      return _buildCameraUnavailable();
    }

    return Stack(
      children: [
        // Live camera preview
        Positioned.fill(
          child: CameraPreview(_cameraController!),
        ),

        // Reference card alignment guide (left side)
        Positioned(
          left: 16,
          top: 20,
          bottom: 20,
          width: 70,
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: Colors.cyan, width: 2),
              borderRadius: BorderRadius.circular(6),
              color: Colors.cyan.withOpacity(0.08),
            ),
            child: const Center(
              child: Text(
                'REF\nCARD',
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontSize: 9,
                    color: Colors.cyan,
                    fontWeight: FontWeight.bold,
                    height: 1.5),
              ),
            ),
          ),
        ),

        // Reaction pouch alignment guide (center-right)
        Positioned(
          left: 100,
          right: 20,
          top: 30,
          bottom: 30,
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: Colors.green, width: 2),
              borderRadius: BorderRadius.circular(8),
              color: Colors.green.withOpacity(0.08),
            ),
            child: const Center(
              child: Text(
                'POUCH TARGET',
                style: TextStyle(
                    fontSize: 11,
                    color: Colors.green,
                    fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ),

        // Capture hint at bottom
        Positioned(
          bottom: 8,
          right: 0,
          left: 0,
          child: Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                'Tap Capture Button',
                style: TextStyle(fontSize: 12, color: Colors.white70),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCameraUnavailable() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(Icons.camera_alt_outlined,
            size: 48, color: Colors.white24),
        const SizedBox(height: 16),
        const Text(
          'Camera unavailable',
          style: TextStyle(fontSize: 16, color: Colors.white54),
        ),
        const SizedBox(height: 8),
        const Text(
          'Camera permission may be denied or no camera hardware detected.',
          style: TextStyle(fontSize: 12, color: Colors.white38),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildUploadPlaceholder() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(Icons.upload_file_outlined,
            size: 56, color: Color(0xFF2563EB)),
        const SizedBox(height: 12),
        const Text(
          'Tap "Upload Image" below',
          style: TextStyle(fontSize: 13, color: Colors.white54),
        ),
        const SizedBox(height: 6),
        const Text(
          'Supports JPG, PNG, HEIC, TIFF, BMP, WEBP & more',
          style: TextStyle(fontSize: 11, color: Colors.white30),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildImagePreview() {
    return Stack(
      fit: StackFit.expand,
      children: [
        Image.file(
          File(_pickedFile!.path),
          fit: BoxFit.cover,
        ),
        Positioned(
          top: 10,
          right: 10,
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFF2563EB).withOpacity(0.85),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              _imageFormatLabel ?? 'IMG',
              style: const TextStyle(
                  fontSize: 11,
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1),
            ),
          ),
        ),
        Positioned(
          top: 10,
          left: 10,
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.black54,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  _captureMode == _CaptureMode.camera
                      ? Icons.camera_alt
                      : Icons.upload_file,
                  size: 12,
                  color: Colors.white70,
                ),
                const SizedBox(width: 4),
                Text(
                  _captureMode == _CaptureMode.camera
                      ? 'Camera'
                      : 'Uploaded',
                  style: const TextStyle(fontSize: 11, color: Colors.white70),
                ),
              ],
            ),
          ),
        ),
        Positioned(
          bottom: 8,
          right: 0,
          left: 0,
          child: Center(
            child: GestureDetector(
              onTap: _captureMode == _CaptureMode.camera
                  ? _captureFromCamera
                  : _uploadFromGallery,
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 14, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white24),
                ),
                child: const Text(
                  'Change image',
                  style: TextStyle(fontSize: 12, color: Colors.white70),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons() {
    if (_captureMode == _CaptureMode.camera) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ElevatedButton.icon(
            onPressed: _hasCameraPermission ? _captureFromCamera : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF1F2937),
              side: const BorderSide(color: Color(0xFF2563EB)),
              padding: const EdgeInsets.symmetric(vertical: 15),
            ),
            icon: const Icon(Icons.camera_alt_outlined,
                color: Color(0xFF60A5FA)),
            label: Text(
              _hasCameraPermission ? 'Capture Image' : 'Camera Unavailable',
              style: const TextStyle(color: Color(0xFF60A5FA)),
            ),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed:
                (_isAnalyzing || _selectedKit == null || _pickedFile == null)
                    ? null
                    : _analyzeImage,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2563EB),
              padding: const EdgeInsets.symmetric(vertical: 16),
              disabledBackgroundColor: const Color(0xFF1E3A5F),
            ),
            icon: _isAnalyzing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                        color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.shutter_speed),
            label: Text(
              _isAnalyzing
                  ? 'Calibrating CIELAB...'
                  : _pickedFile == null
                      ? 'Capture Image First'
                      : 'Classify Reaction',
            ),
          ),
        ],
      );
    } else {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ElevatedButton.icon(
            onPressed: _uploadFromGallery,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF1F2937),
              side: const BorderSide(color: Color(0xFF06B6D4)),
              padding: const EdgeInsets.symmetric(vertical: 15),
            ),
            icon: const Icon(Icons.upload_file_outlined,
                color: Color(0xFF06B6D4)),
            label: const Text('Upload Image',
                style: TextStyle(color: Color(0xFF06B6D4))),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed:
                (_isAnalyzing || _selectedKit == null || _pickedFile == null)
                    ? null
                    : _analyzeImage,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2563EB),
              padding: const EdgeInsets.symmetric(vertical: 16),
              disabledBackgroundColor: const Color(0xFF1E3A5F),
            ),
            icon: _isAnalyzing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                        color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.analytics_outlined),
            label: Text(
              _isAnalyzing
                  ? 'Calibrating CIELAB...'
                  : _pickedFile == null
                      ? 'Upload Image First'
                      : 'Classify Reaction',
            ),
          ),
        ],
      );
    }
  }

  Widget _buildResultCard() {
    final bool positive =
        (_analysisResult!['classification_result'] as String)
            .contains('POSITIVE');
    final color = positive ? Colors.red : Colors.green;
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: color.withOpacity(0.10),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: color, width: 2),
          ),
          child: Column(
            children: [
              Icon(
                positive
                    ? Icons.warning_amber_rounded
                    : Icons.check_circle_outline,
                size: 48,
                color: color,
              ),
              const SizedBox(height: 8),
              Text(
                (_analysisResult!['classification_result'] as String)
                    .replaceAll('_', ' '),
                style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: color),
              ),
              const SizedBox(height: 4),
              Text(
                'Analyte: ${_analysisResult!['analyte_detected']}',
                style: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF1F2937),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white12),
                ),
                child: Text(
                  'Source: ${_analysisResult!['source']}',
                  style: const TextStyle(
                      fontSize: 11, color: Colors.white54),
                ),
              ),
              const SizedBox(height: 10),
              Text(
                _analysisResult!['classification_reason'],
                textAlign: TextAlign.center,
                style:
                    const TextStyle(fontSize: 12, color: Colors.white60),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.orange.withOpacity(0.08),
            borderRadius: BorderRadius.circular(10),
            border:
                Border.all(color: Colors.orange.withOpacity(0.4)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.info_outline,
                  size: 16, color: Colors.orange),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  _analysisResult!['disclaimer'],
                  style: const TextStyle(
                      fontSize: 11, color: Colors.orange),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}