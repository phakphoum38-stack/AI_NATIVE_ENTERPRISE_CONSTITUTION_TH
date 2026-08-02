import 'package:flutter/foundation.dart';

class AiEvidenceRecord {
  const AiEvidenceRecord({
    required this.id,
    required this.timestamp,
    required this.action,
    required this.providerId,
    required this.model,
    required this.result,
    this.details = const <String, Object?>{},
  });

  final String id;
  final DateTime timestamp;
  final String action;
  final String providerId;
  final String model;
  final String result;
  final Map<String, Object?> details;
}

class AiEvidenceLog extends ChangeNotifier {
  final List<AiEvidenceRecord> _records = <AiEvidenceRecord>[];

  List<AiEvidenceRecord> get records => List.unmodifiable(_records.reversed);

  void add(AiEvidenceRecord record) {
    _records.add(record);
    notifyListeners();
  }

  void clear() {
    if (_records.isEmpty) return;
    _records.clear();
    notifyListeners();
  }
}
