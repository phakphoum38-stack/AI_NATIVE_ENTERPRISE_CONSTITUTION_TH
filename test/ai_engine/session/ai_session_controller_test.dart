import 'package:ai_native_enterprise_constitution/ai_engine/orchestration/ai_orchestrator.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_controller.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_registry.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/local_demo_ai_provider.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/session/ai_session_controller.dart';
import 'package:ai_native_enterprise_constitution/core/evidence/evidence_log.dart';
import 'package:ai_native_enterprise_constitution/core/policy/ai_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late LocalDemoAiProvider provider;
  late AiProviderController providerController;
  late AiEvidenceLog evidenceLog;
  late AiSessionController sessionController;

  setUp(() async {
    provider = LocalDemoAiProvider();
    providerController = AiProviderController(AiProviderRegistry([provider]));
    evidenceLog = AiEvidenceLog();
    sessionController = AiSessionController(
      orchestrator: AiOrchestrator(
        providerController: providerController,
        policy: const AiExecutionPolicy(),
        evidenceLog: evidenceLog,
      ),
    );
    await providerController.selectProvider(provider.id);
  });

  test('sends governed message and records evidence', () async {
    await sessionController.send('hello enterprise');

    expect(sessionController.messages, hasLength(2));
    expect(sessionController.messages.first.role, 'user');
    expect(sessionController.messages.last.role, 'assistant');
    expect(sessionController.messages.last.text, contains('hello enterprise'));
    expect(evidenceLog.records, hasLength(1));
    expect(evidenceLog.records.single.result, 'success');
  });

  test('high risk requires explicit approval', () async {
    sessionController.setRiskLevel(AiRiskLevel.high);

    expect(sessionController.evaluateCurrentPolicy().requiresApproval, isTrue);
    await expectLater(
      sessionController.send('high risk operation'),
      throwsStateError,
    );

    await sessionController.send('approved operation', approved: true);
    expect(sessionController.messages.last.role, 'assistant');
  });

  test('restricted privacy is blocked', () async {
    sessionController.setPrivacyLevel(AiPrivacyLevel.restricted);

    expect(sessionController.evaluateCurrentPolicy().allowed, isFalse);
    await expectLater(
      sessionController.send('restricted payload'),
      throwsStateError,
    );
  });

  test('evidence log notifies listeners', () {
    var notifications = 0;
    evidenceLog.addListener(() => notifications += 1);

    evidenceLog.add(
      AiEvidenceRecord(
        id: 'record-1',
        timestamp: DateTime.utc(2026),
        action: 'test',
        providerId: 'local-demo',
        model: 'local-demo-v1',
        result: 'success',
      ),
    );
    evidenceLog.clear();

    expect(notifications, 2);
  });
}
