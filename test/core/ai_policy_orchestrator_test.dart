import 'package:ai_native_enterprise_constitution/ai_engine/models/ai_exchange.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/orchestration/ai_orchestrator.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_controller.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_registry.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/local_demo_ai_provider.dart';
import 'package:ai_native_enterprise_constitution/core/evidence/evidence_log.dart';
import 'package:ai_native_enterprise_constitution/core/policy/ai_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AiExecutionPolicy', () {
    const policy = AiExecutionPolicy();

    test('blocks restricted data', () {
      final decision = policy.evaluate(
        const AiExecutionContext(
          privacyLevel: AiPrivacyLevel.restricted,
          riskLevel: AiRiskLevel.low,
        ),
      );

      expect(decision.allowed, isFalse);
    });

    test('requires approval for high-risk requests', () {
      final decision = policy.evaluate(
        const AiExecutionContext(
          privacyLevel: AiPrivacyLevel.localOnly,
          riskLevel: AiRiskLevel.high,
        ),
      );

      expect(decision.allowed, isTrue);
      expect(decision.requiresApproval, isTrue);
    });
  });

  group('AiOrchestrator', () {
    test('sends through the active provider and records evidence', () async {
      final provider = LocalDemoAiProvider();
      final controller = AiProviderController(AiProviderRegistry([provider]));
      final evidence = AiEvidenceLog();
      final orchestrator = AiOrchestrator(
        providerController: controller,
        policy: const AiExecutionPolicy(),
        evidenceLog: evidence,
      );
      await controller.selectProvider(provider.id);

      final response = await orchestrator.send(
        request: const AiRequest(id: 'request-1', prompt: 'hello'),
        context: const AiExecutionContext(
          privacyLevel: AiPrivacyLevel.localOnly,
          riskLevel: AiRiskLevel.low,
        ),
      );

      expect(response.requestId, 'request-1');
      expect(evidence.records, hasLength(1));
      expect(evidence.records.single.result, 'success');
    });

    test('does not call provider when policy blocks the request', () async {
      final provider = LocalDemoAiProvider();
      final controller = AiProviderController(AiProviderRegistry([provider]));
      final evidence = AiEvidenceLog();
      final orchestrator = AiOrchestrator(
        providerController: controller,
        policy: const AiExecutionPolicy(),
        evidenceLog: evidence,
      );
      await controller.selectProvider(provider.id);

      await expectLater(
        orchestrator.send(
          request: const AiRequest(id: 'request-2', prompt: 'secret'),
          context: const AiExecutionContext(
            privacyLevel: AiPrivacyLevel.restricted,
            riskLevel: AiRiskLevel.low,
          ),
        ),
        throwsStateError,
      );

      expect(evidence.records, isEmpty);
    });
  });
}
