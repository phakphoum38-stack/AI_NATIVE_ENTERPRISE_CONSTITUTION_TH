import '../ai_engine/orchestration/ai_orchestrator.dart';
import '../ai_engine/providers/ai_provider_controller.dart';
import '../ai_engine/providers/ai_provider_registry.dart';
import '../ai_engine/providers/local_demo_ai_provider.dart';
import '../ai_engine/session/ai_session_controller.dart';
import '../core/evidence/evidence_log.dart';
import '../core/policy/ai_policy.dart';

class AppDependencies {
  AppDependencies._({
    required this.aiProviderController,
    required this.aiOrchestrator,
    required this.aiSessionController,
    required this.evidenceLog,
  });

  final AiProviderController aiProviderController;
  final AiOrchestrator aiOrchestrator;
  final AiSessionController aiSessionController;
  final AiEvidenceLog evidenceLog;

  factory AppDependencies.create() {
    final registry = AiProviderRegistry(<LocalDemoAiProvider>[
      LocalDemoAiProvider(),
    ]);
    final providerController = AiProviderController(registry);
    final evidenceLog = AiEvidenceLog();
    final orchestrator = AiOrchestrator(
      providerController: providerController,
      policy: const AiExecutionPolicy(),
      evidenceLog: evidenceLog,
    );
    final sessionController = AiSessionController(orchestrator: orchestrator);

    return AppDependencies._(
      aiProviderController: providerController,
      aiOrchestrator: orchestrator,
      aiSessionController: sessionController,
      evidenceLog: evidenceLog,
    );
  }
}
