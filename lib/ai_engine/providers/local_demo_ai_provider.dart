import 'ai_provider.dart';

class LocalDemoAiProvider implements AiProvider {
  LocalDemoAiProvider({this.model = 'local-demo-v1'});

  @override
  final String model;

  bool _connected = false;

  @override
  String get id => 'local-demo';

  @override
  String get displayName => 'Local Demo';

  @override
  AiProviderCapabilities get capabilities => const AiProviderCapabilities(
        text: true,
        streaming: true,
        structuredOutput: true,
        localProcessing: true,
      );

  @override
  Future<void> connect() async {
    _connected = true;
  }

  @override
  Future<void> disconnect() async {
    _connected = false;
  }

  @override
  Future<bool> checkHealth() async => _connected;

  @override
  Future<List<String>> listModels() async => const ['local-demo-v1'];
}
