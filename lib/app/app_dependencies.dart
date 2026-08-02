import '../ai_engine/orchestration/ai_orchestrator.dart';
import '../ai_engine/providers/ai_provider_controller.dart';
import '../ai_engine/providers/ai_provider_registry.dart';
import '../ai_engine/providers/local_demo_ai_provider.dart';
import '../core/evidence/evidence_log.dart';
import '../core/policy/ai_policy.dart';

class AppDependencies {
  AppDependencies._({
    required this.aiProviderController,
    required this.aiOrchestrator,
    required this.evidenceLog,
  });

  final AiProviderController aiProviderController;
  final AiOrchestrator aiOrchestrator;
  final AiEvidenceLog evidenceLog;

  factory AppDependencies.create() {
    final registry = AiProviderRegistry(<LocalDemoAiProvider>[
      LocalDemoAiProvider(),
    ]);
    final controller = AiProviderController(registry);
    final evidenceLog = AiEvidenceLog();
    final orchestrator = AiOrchestrator(
      providerController: controller,
      policy: const AiExecutionPolicy(),
      evidenceLog: evidenceLog,
    );

    return AppDependencies._(
      aiProviderController: controller,
      aiOrchestrator: orchestrator,
      evidenceLog: evidenceLog,
    );
  }
}
