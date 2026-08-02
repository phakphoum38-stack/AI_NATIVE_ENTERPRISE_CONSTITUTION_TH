import 'ai_provider.dart';

class AiProviderRegistry {
  AiProviderRegistry(Iterable<AiProvider> providers)
    : _providers = {for (final provider in providers) provider.id: provider};

  final Map<String, AiProvider> _providers;

  List<AiProvider> get providers => List.unmodifiable(_providers.values);

  AiProvider? findById(String id) => _providers[id];

  void register(AiProvider provider) {
    if (_providers.containsKey(provider.id)) {
      throw StateError('AI provider "${provider.id}" is already registered.');
    }
    _providers[provider.id] = provider;
  }
}
