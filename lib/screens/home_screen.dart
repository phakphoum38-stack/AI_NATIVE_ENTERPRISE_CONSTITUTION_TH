import 'package:flutter/material.dart';

import '../ai_engine/providers/ai_provider.dart';
import '../ai_engine/providers/ai_provider_controller.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({required this.controller, super.key});

  final AiProviderController controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Native Enterprise'),
        actions: [
          ListenableBuilder(
            listenable: controller,
            builder: (context, _) => Padding(
              padding: const EdgeInsets.only(right: 16),
              child: _StatusChip(status: controller.status),
            ),
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: controller,
        builder: (context, _) {
          final provider = controller.activeProvider;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(
                'Universal AI Provider Foundation',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              const Text(
                'Provider เปลี่ยนได้ แต่ Core, Policy, Privacy และหลักฐานต้องคงที่',
              ),
              const SizedBox(height: 24),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'AI Provider Control',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        value: provider?.id,
                        decoration: const InputDecoration(
                          labelText: 'Provider',
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          for (final item in controller.registry.providers)
                            DropdownMenuItem(
                              value: item.id,
                              child: Text(item.displayName),
                            ),
                        ],
                        onChanged: controller.status ==
                                AiProviderConnectionStatus.connecting
                            ? null
                            : (value) {
                                if (value != null) {
                                  _selectProvider(context, value);
                                }
                              },
                      ),
                      const SizedBox(height: 16),
                      _ProviderDetails(provider: provider),
                      if (controller.errorMessage case final message?) ...[
                        const SizedBox(height: 12),
                        Text(
                          message,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
                          ),
                        ),
                      ],
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: [
                          FilledButton.icon(
                            onPressed: provider == null
                                ? null
                                : () => _selectProvider(context, provider.id),
                            icon: const Icon(Icons.health_and_safety_outlined),
                            label: const Text('ตรวจสุขภาพ'),
                          ),
                          OutlinedButton.icon(
                            onPressed: provider == null
                                ? null
                                : controller.disconnect,
                            icon: const Icon(Icons.link_off),
                            label: const Text('ตัดการเชื่อมต่อ'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const _PrinciplesCard(),
            ],
          );
        },
      ),
    );
  }

  Future<void> _selectProvider(BuildContext context, String providerId) async {
    try {
      await controller.selectProvider(providerId);
    } catch (_) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('เชื่อมต่อ AI Provider ไม่สำเร็จ')),
      );
    }
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final AiProviderConnectionStatus status;

  @override
  Widget build(BuildContext context) {
    final label = switch (status) {
      AiProviderConnectionStatus.disconnected => 'Disconnected',
      AiProviderConnectionStatus.connecting => 'Connecting',
      AiProviderConnectionStatus.connected => 'Connected',
      AiProviderConnectionStatus.error => 'Error',
    };
    return Chip(label: Text(label));
  }
}

class _ProviderDetails extends StatelessWidget {
  const _ProviderDetails({required this.provider});

  final AiProvider? provider;

  @override
  Widget build(BuildContext context) {
    if (provider == null) {
      return const Text('ยังไม่ได้เลือก Provider');
    }
    final capabilities = provider!.capabilities;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Model: ${provider!.model}'),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            if (capabilities.text) const Chip(label: Text('Text')),
            if (capabilities.streaming) const Chip(label: Text('Streaming')),
            if (capabilities.toolCalling) const Chip(label: Text('Tools')),
            if (capabilities.structuredOutput)
              const Chip(label: Text('Structured Output')),
            if (capabilities.vision) const Chip(label: Text('Vision')),
            if (capabilities.audio) const Chip(label: Text('Audio')),
            if (capabilities.localProcessing)
              const Chip(label: Text('Local Only')),
          ],
        ),
      ],
    );
  }
}

class _PrinciplesCard extends StatelessWidget {
  const _PrinciplesCard();

  @override
  Widget build(BuildContext context) {
    const principles = [
      'Long-term First',
      'One Truth',
      'AI is a Team Member',
      'Every Change Has Evidence',
      'Documentation Never Lags Behind Code',
      'Quality Is Continuous',
      'Provider Independent',
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Constitution Principles',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            for (final principle in principles)
              ListTile(
                dense: true,
                leading: const Icon(Icons.verified_outlined),
                title: Text(principle),
              ),
          ],
        ),
      ),
    );
  }
}
