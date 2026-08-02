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
      await _requireHealthy(next);
      _activeProvider = next;
      _status = AiProviderConnectionStatus.connected;
    } catch (error) {
      await _restorePrevious(previous);
      _errorMessage = error.toString();
      rethrow;
    } finally {
      notifyListeners();
    }
  }

  Future<void> refreshHealth() async {
    final provider = _activeProvider;
    if (provider == null) {
      throw StateError('No active AI provider.');
    }

    _status = AiProviderConnectionStatus.connecting;
    _errorMessage = null;
    notifyListeners();

    try {
      await _requireHealthy(provider);
      _status = AiProviderConnectionStatus.connected;
    } catch (error) {
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

  Future<void> _requireHealthy(AiProvider provider) async {
    final healthy = await provider.checkHealth();
    if (!healthy) {
      throw StateError('${provider.displayName} health check failed.');
    }
  }

  Future<void> _restorePrevious(AiProvider? previous) async {
    _activeProvider = previous;
    if (previous == null) {
      _status = AiProviderConnectionStatus.error;
      return;
    }

    try {
      await previous.connect();
      await _requireHealthy(previous);
      _status = AiProviderConnectionStatus.connected;
    } catch (_) {
      _status = AiProviderConnectionStatus.error;
    }
  }
}
