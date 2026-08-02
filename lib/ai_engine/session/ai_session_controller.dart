import 'package:flutter/foundation.dart';

import '../../core/policy/ai_policy.dart';
import '../models/ai_exchange.dart';
import '../orchestration/ai_orchestrator.dart';

class AiConversationMessage {
  const AiConversationMessage({
    required this.id,
    required this.role,
    required this.text,
    required this.timestamp,
    this.providerId,
    this.model,
  });

  final String id;
  final String role;
  final String text;
  final DateTime timestamp;
  final String? providerId;
  final String? model;
}

class AiSessionController extends ChangeNotifier {
  AiSessionController({required this.orchestrator});

  final AiOrchestrator orchestrator;

  final List<AiConversationMessage> _messages = <AiConversationMessage>[];
  AiPrivacyLevel _privacyLevel = AiPrivacyLevel.localOnly;
  AiRiskLevel _riskLevel = AiRiskLevel.low;
  bool _containsSensitiveData = false;
  bool _requiresTools = false;
  bool _isSending = false;
  String? _activeRequestId;
  String? _errorMessage;

  List<AiConversationMessage> get messages => List.unmodifiable(_messages);
  AiPrivacyLevel get privacyLevel => _privacyLevel;
  AiRiskLevel get riskLevel => _riskLevel;
  bool get containsSensitiveData => _containsSensitiveData;
  bool get requiresTools => _requiresTools;
  bool get isSending => _isSending;
  String? get errorMessage => _errorMessage;

  void setPrivacyLevel(AiPrivacyLevel value) {
    _privacyLevel = value;
    notifyListeners();
  }

  void setRiskLevel(AiRiskLevel value) {
    _riskLevel = value;
    notifyListeners();
  }

  void setContainsSensitiveData(bool value) {
    _containsSensitiveData = value;
    notifyListeners();
  }

  void setRequiresTools(bool value) {
    _requiresTools = value;
    notifyListeners();
  }

  AiPolicyDecision evaluateCurrentPolicy() {
    return const AiExecutionPolicy().evaluate(_executionContext);
  }

  Future<void> send(String prompt, {bool approved = false}) async {
    final text = prompt.trim();
    if (text.isEmpty || _isSending) return;

    final requestId = 'req_${DateTime.now().microsecondsSinceEpoch}';
    _activeRequestId = requestId;
    _messages.add(
      AiConversationMessage(
        id: '${requestId}_user',
        role: 'user',
        text: text,
        timestamp: DateTime.now().toUtc(),
      ),
    );
    _isSending = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await orchestrator.send(
        request: AiRequest(id: requestId, prompt: text),
        context: _executionContext,
        approved: approved,
      );
      _messages.add(
        AiConversationMessage(
          id: '${requestId}_assistant',
          role: 'assistant',
          text: response.text,
          timestamp: DateTime.now().toUtc(),
          providerId: response.providerId,
          model: response.model,
        ),
      );
    } catch (error) {
      _errorMessage = error.toString();
      rethrow;
    } finally {
      _activeRequestId = null;
      _isSending = false;
      notifyListeners();
    }
  }

  Future<void> cancel() async {
    final requestId = _activeRequestId;
    if (requestId == null) return;
    await orchestrator.cancel(requestId);
  }

  void clearConversation() {
    _messages.clear();
    _errorMessage = null;
    notifyListeners();
  }

  AiExecutionContext get _executionContext => AiExecutionContext(
    privacyLevel: _privacyLevel,
    riskLevel: _riskLevel,
    containsSensitiveData: _containsSensitiveData,
    requiresTools: _requiresTools,
  );
}
