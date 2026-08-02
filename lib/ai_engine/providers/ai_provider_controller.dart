import 'package:flutter/foundation.dart';

import 'ai_provider.dart';
import 'ai_provider_registry.dart';

class AiProviderController extends ChangeNotifier {
  AiProviderController(this.registry);

  final AiProviderRegistry registry;

  AiProvider? _activeProvider;
  AiProviderConnectionStatus _status =
      AiProviderConnectionStatus.disconnected;
  String? _errorMessage;

  AiProvider? get activeProvider => _activeProvider;
  AiProviderConnectionStatus get status => _status;
  String? get errorMessage => _errorMessage;

  Future<void> selectProvider(String providerId) async {
    final next = registry.findById(providerId);
    if (next == null) {
      throw ArgumentError.value(providerId, 'providerId', 'Unknown provider');
    }

    if (identical(next, _activeProvider) &&
        _status == AiProviderConnectionStatus.connected) {
      return;
    }

    final previous = _activeProvider;
    _status = AiProviderConnectionStatus.connecting;
    _errorMessage = null;
    notifyListeners();

    try {
      await previous?.disconnect();
      await next.connect();
      final healthy = await next.checkHealth();
      if (!healthy) {
        throw StateError('${next.displayName} health check failed.');
      }
      _activeProvider = next;
      _status = AiProviderConnectionStatus.connected;
    } catch (error) {
      _activeProvider = previous;
      _status = AiProviderConnectionStatus.error;
      _errorMessage = error.toString();
      rethrow;
    } finally {
      notifyListeners();
    }
  }

  Future<void> disconnect() async {
    await _activeProvider?.disconnect();
    _activeProvider = null;
    _status = AiProviderConnectionStatus.disconnected;
    _errorMessage = null;
    notifyListeners();
  }
}
