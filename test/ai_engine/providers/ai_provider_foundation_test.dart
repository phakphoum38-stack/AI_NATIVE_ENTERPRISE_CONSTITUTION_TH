import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_controller.dart';
import 'package:ai_native_enterprise_constitution/ai_engine/providers/ai_provider_registry.dart';
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

    test('reports an error when health check fails', () async {
      final provider = _FakeProvider(id: 'broken', healthy: false);
      final controller = AiProviderController(AiProviderRegistry([provider]));

      await expectLater(
        controller.selectProvider('broken'),
        throwsStateError,
      );

      expect(controller.status, AiProviderConnectionStatus.error);
      expect(controller.activeProvider, isNull);
      expect(controller.errorMessage, isNotNull);
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
}

class _FakeProvider implements AiProvider {
  _FakeProvider({required this.id, this.healthy = true});

  @override
  final String id;

  final bool healthy;
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
}
