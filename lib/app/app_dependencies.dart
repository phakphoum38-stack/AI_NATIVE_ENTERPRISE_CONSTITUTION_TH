import '../ai_engine/providers/ai_provider_controller.dart';
import '../ai_engine/providers/ai_provider_registry.dart';
import '../ai_engine/providers/local_demo_ai_provider.dart';

class AppDependencies {
  AppDependencies._({required this.aiProviderController});

  final AiProviderController aiProviderController;

  factory AppDependencies.create() {
    final registry = AiProviderRegistry([LocalDemoAiProvider()]);
    return AppDependencies._(
      aiProviderController: AiProviderController(registry),
    );
  }
}
