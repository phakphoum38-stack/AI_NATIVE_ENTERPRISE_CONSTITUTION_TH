class AiRequest {
  const AiRequest({
    required this.id,
    required this.prompt,
    this.systemInstruction,
  });

  final String id;
  final String prompt;
  final String? systemInstruction;
}

class AiUsage {
  const AiUsage({
    required this.inputTokens,
    required this.outputTokens,
    this.estimatedCostUsd = 0,
  });

  final int inputTokens;
  final int outputTokens;
  final double estimatedCostUsd;

  int get totalTokens => inputTokens + outputTokens;
}

class AiResponse {
  const AiResponse({
    required this.requestId,
    required this.text,
    required this.providerId,
    required this.model,
    required this.usage,
  });

  final String requestId;
  final String text;
  final String providerId;
  final String model;
  final AiUsage usage;
}
