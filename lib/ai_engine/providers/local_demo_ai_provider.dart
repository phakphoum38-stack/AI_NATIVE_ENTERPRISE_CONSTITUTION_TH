import '../models/ai_exchange.dart';
import 'ai_provider.dart';

class LocalDemoAiProvider implements AiProvider {
  LocalDemoAiProvider({this.model = 'local-demo-v1'});

  @override
  final String model;

  bool _connected = false;
  final Set<String> _cancelledRequests = <String>{};

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

  @override
  Future<AiResponse> sendMessage(AiRequest request) async {
    _requireConnected();
    if (_cancelledRequests.remove(request.id)) {
      throw StateError('Request ${request.id} was cancelled.');
    }

    final text = 'Local demo response: ${request.prompt.trim()}';
    return AiResponse(
      requestId: request.id,
      text: text,
      providerId: id,
      model: model,
      usage: AiUsage(
        inputTokens: estimateTokens(request.prompt),
        outputTokens: estimateTokens(text),
      ),
    );
  }

  @override
  Stream<String> streamMessage(AiRequest request) async* {
    _requireConnected();
    final words = 'Local demo response: ${request.prompt.trim()}'.split(' ');
    for (final word in words) {
      if (_cancelledRequests.remove(request.id)) return;
      yield '$word ';
    }
  }

  @override
  Future<void> cancelRequest(String requestId) async {
    _cancelledRequests.add(requestId);
  }

  @override
  int estimateTokens(String text) {
    final normalized = text.trim();
    if (normalized.isEmpty) return 0;
    return (normalized.length / 4).ceil();
  }

  void _requireConnected() {
    if (!_connected) {
      throw StateError('Local Demo is not connected.');
    }
  }
}
