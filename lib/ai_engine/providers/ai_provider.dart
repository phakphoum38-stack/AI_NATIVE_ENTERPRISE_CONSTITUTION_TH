import '../models/ai_exchange.dart';

enum AiProviderConnectionStatus { disconnected, connecting, connected, error }

class AiProviderCapabilities {
  const AiProviderCapabilities({
    this.text = true,
    this.streaming = false,
    this.toolCalling = false,
    this.structuredOutput = false,
    this.vision = false,
    this.audio = false,
    this.localProcessing = false,
  });

  final bool text;
  final bool streaming;
  final bool toolCalling;
  final bool structuredOutput;
  final bool vision;
  final bool audio;
  final bool localProcessing;
}

abstract interface class AiProvider {
  String get id;
  String get displayName;
  String get model;
  AiProviderCapabilities get capabilities;

  Future<void> connect();
  Future<void> disconnect();
  Future<bool> checkHealth();
  Future<List<String>> listModels();
  Future<AiResponse> sendMessage(AiRequest request);
  Stream<String> streamMessage(AiRequest request);
  Future<void> cancelRequest(String requestId);
  int estimateTokens(String text);
}
