import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/test_record.dart';
import 'capture_screen.dart';

class DashboardScreen extends StatefulWidget {
  final Map<String, dynamic> user;
  const DashboardScreen({super.key, required this.user});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<MobileTestRecord> _tests = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void _loadData() async {
    setState(() => _isLoading = true);
    try {
      final tests = await apiService.fetchTests();
      setState(() => _tests = tests);
    } catch (e) {
      // offline or error
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Forensic Field Node', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        backgroundColor: const Color(0xFF111827),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Operator Info Card
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const CircleAvatar(
                          backgroundColor: Color(0xFF2563EB),
                          child: Icon(Icons.badge, color: Colors.white),
                        ),
                        const SizedBox(width: 14),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(widget.user['full_name'] ?? 'Officer', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                            Text('Badge: ${widget.user['badge_number'] ?? 'N/A'} • ${widget.user['role']}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // New Test Action Card
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const CaptureScreen()),
                    ).then((_) => _loadData());
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0891B2),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  icon: const Icon(Icons.camera_alt, color: Colors.white),
                  label: const Text('Initiate New Field Test', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                ),
                const SizedBox(height: 24),
                const Text('Recent Field Tests', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.grey)),
                const SizedBox(height: 8),
                if (_tests.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 32),
                    child: Center(child: Text('No field tests conducted yet', style: TextStyle(color: Colors.grey))),
                  )
                else
                  ..._tests.map((t) => Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      title: Text(t.testId, style: const TextStyle(fontWeight: FontWeight.bold, fontFamily: 'monospace')),
                      subtitle: Text('${t.kitName} • ${t.classificationResult.replaceAll('PRESUMPTIVE_', '')}'),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: t.classificationResult == 'PRESUMPTIVE_POSITIVE' ? Colors.red.withOpacity(0.2) : Colors.green.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                            color: t.classificationResult == 'PRESUMPTIVE_POSITIVE' ? Colors.red : Colors.green,
                          ),
                        ),
                        child: Text(
                          t.classificationResult.replaceAll('PRESUMPTIVE_', ''),
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: t.classificationResult == 'PRESUMPTIVE_POSITIVE' ? Colors.redAccent : Colors.greenAccent,
                          ),
                        ),
                      ),
                    ),
                  )),
              ],
            ),
    );
  }
}
