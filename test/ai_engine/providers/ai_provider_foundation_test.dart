import 'package:ai_native_enterprise_constitution/ai_engine/models/ai_exchange.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_controller.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_registry.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/local_demo_ai_provider.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AiProviderRegistry', () {
    test('finds a registered provider by id', () {
      final provider = _FakeProvider(id: 'local');
      final registry = AiProviderRegistry([provider]);

      expect(registry.findById('local'), same(provider));
      expect(registry.providers, contains(provider));
    });

    test('rejects duplicate provider ids', () {
      final registry = AiProviderRegistry([_FakeProvider(id: 'local')]);

      expect(
        () => registry.register(_FakeProvider(id: 'local')),
        throwsStateError,
      );
    });
  });

  group('AiProviderController', () {
    test('connects and selects a healthy provider', () async {
      final provider = _FakeProvider(id: 'primary');
      final controller = AiProviderController(AiProviderRegistry([provider]));

      await controller.selectProvider('primary');

      expect(controller.activeProvider, same(provider));
      expect(controller.status, AiProviderConnectionStatus.connected);
      expect(provider.connectCalls, 1);
      expect(provider.healthCalls, 1);
    });

    test('reports an error when first provider health check fails', () async {
      final provider = _FakeProvider(id: 'broken', healthy: false);
      final controller = AiProviderController(AiProviderRegistry([provider]));

      await expectLater(controller.selectProvider('broken'), throwsStateError);

      expect(controller.status, AiProviderConnectionStatus.error);
      expect(controller.activeProvider, isNull);
      expect(controller.errorMessage, isNotNull);
    });

    test('restores previous provider when switching fails', () async {
      final primary = _FakeProvider(id: 'primary');
      final broken = _FakeProvider(id: 'broken', healthy: false);
      final controller = AiProviderController(
        AiProviderRegistry([primary, broken]),
      );
      await controller.selectProvider('primary');

      await expectLater(controller.selectProvider('broken'), throwsStateError);

      expect(controller.activeProvider, same(primary));
      expect(controller.status, AiProviderConnectionStatus.connected);
      expect(primary.connectCalls, 2);
    });

    test('refreshes active provider health', () async {
      final provider = _FakeProvider(id: 'primary');
      final controller = AiProviderController(AiProviderRegistry([provider]));
      await controller.selectProvider('primary');

      await controller.refreshHealth();

      expect(controller.status, AiProviderConnectionStatus.connected);
      expect(provider.healthCalls, 2);
    });

    test('disconnect clears provider state', () async {
      final provider = _FakeProvider(id: 'primary');
      final controller = AiProviderController(AiProviderRegistry([provider]));
      await controller.selectProvider('primary');

      await controller.disconnect();

      expect(controller.activeProvider, isNull);
      expect(controller.status, AiProviderConnectionStatus.disconnected);
      expect(provider.disconnectCalls, 1);
    });
  });

  group('LocalDemoAiProvider', () {
    test('returns provider-neutral response and usage', () async {
      final provider = LocalDemoAiProvider();
      await provider.connect();

      final response = await provider.sendMessage(
        const AiRequest(id: 'request-1', prompt: 'hello enterprise'),
      );

      expect(response.requestId, 'request-1');
      expect(response.providerId, provider.id);
      expect(response.text, contains('hello enterprise'));
      expect(response.usage.totalTokens, greaterThan(0));
    });

    test('requires connection before sending', () async {
      final provider = LocalDemoAiProvider();

      await expectLater(
        provider.sendMessage(const AiRequest(id: 'r', prompt: 'hello')),
        throwsStateError,
      );
    });
  });
}

class _FakeProvider implements AiProvider {
  _FakeProvider({required this.id, this.healthy = true});

  @override
  final String id;

  bool healthy;
  int connectCalls = 0;
  int disconnectCalls = 0;
  int healthCalls = 0;

  @override
  AiProviderCapabilities get capabilities => const AiProviderCapabilities();

  @override
  String get displayName => id;

  @override
  String get model => 'test-model';

  @override
  Future<bool> checkHealth() async {
    healthCalls += 1;
    return healthy;
  }

  @override
  Future<void> connect() async {
    connectCalls += 1;
  }

  @override
  Future<void> disconnect() async {
    disconnectCalls += 1;
  }

  @override
  Future<List<String>> listModels() async => const ['test-model'];

  @override
  Future<AiResponse> sendMessage(AiRequest request) async => AiResponse(
        requestId: request.id,
        text: request.prompt,
        providerId: id,
        model: model,
        usage: const AiUsage(inputTokens: 1, outputTokens: 1),
      );

  @override
  Stream<String> streamMessage(AiRequest request) => Stream.value(request.prompt);

  @override
  Future<void> cancelRequest(String requestId) async {}

  @override
  int estimateTokens(String text) => text.isEmpty ? 0 : 1;
}
