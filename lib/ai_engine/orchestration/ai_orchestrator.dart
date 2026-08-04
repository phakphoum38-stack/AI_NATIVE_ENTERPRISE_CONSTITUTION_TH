import '../../core/evidence/evidence_log.dart';
import '../../core/policy/ai_policy.dart';
import '../models/ai_exchange.dart';
import '../providers/ai_provider_controller.dart';

class AiOrchestrator {
  AiOrchestrator({
    required this.providerController,
    required this.policy,
    required this.evidenceLog,
    this.shouldRetainEvidence,
  });

  final AiProviderController providerController;
  final AiExecutionPolicy policy;
  final AiEvidenceLog evidenceLog;
  final bool Function()? shouldRetainEvidence;

  Future<AiResponse> send({
    required AiRequest request,
    required AiExecutionContext context,
    bool approved = false,
  }) async {
    final decision = policy.evaluate(context);
    if (!decision.allowed) {
      throw StateError(decision.reason ?? 'AI request blocked by policy.');
    }
    if (decision.requiresApproval && !approved) {
      throw StateError('User approval is required before this AI request.');
    }

    final provider = providerController.activeProvider;
    if (provider == null) {
      throw StateError('No active AI provider is connected.');
    }

    try {
      final response = await provider.sendMessage(request);
      _recordEvidence(
        AiEvidenceRecord(
          id: request.id,
          timestamp: DateTime.now().toUtc(),
          action: 'ai.message.send',
          providerId: provider.id,
          model: provider.model,
          result: 'success',
          details: <String, Object?>{
            'privacyLevel': context.privacyLevel.name,
            'riskLevel': context.riskLevel.name,
            'inputTokens': response.usage.inputTokens,
            'outputTokens': response.usage.outputTokens,
          },
        ),
      );
      return response;
    } catch (error) {
      _recordEvidence(
        AiEvidenceRecord(
          id: request.id,
          timestamp: DateTime.now().toUtc(),
          action: 'ai.message.send',
          providerId: provider.id,
          model: provider.model,
          result: 'failure',
          details: <String, Object?>{'error': error.toString()},
        ),
      );
      rethrow;
    }
  }

  Future<void> cancel(String requestId) async {
    final provider = providerController.activeProvider;
    if (provider == null) {
      throw StateError('No active AI provider is connected.');
    }
    await provider.cancelRequest(requestId);
  }

  void _recordEvidence(AiEvidenceRecord record) {
    if (shouldRetainEvidence?.call() ?? true) {
      evidenceLog.add(record);
    }
  }
}
