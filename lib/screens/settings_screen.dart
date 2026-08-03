import 'package:flutter/material.dart';

import '../app/app_settings.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({required this.controller, super.key});

  final AppSettingsController controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListenableBuilder(
        listenable: controller,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text('Appearance', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            SegmentedButton<ThemeMode>(
              segments: const [
                ButtonSegment(value: ThemeMode.system, label: Text('System')),
                ButtonSegment(value: ThemeMode.light, label: Text('Light')),
                ButtonSegment(value: ThemeMode.dark, label: Text('Dark')),
              ],
              selected: {controller.themeMode},
              onSelectionChanged: (selection) {
                controller.setThemeMode(selection.single);
              },
            ),
            const SizedBox(height: 24),
            DropdownButtonFormField<AppLanguage>(
              initialValue: controller.language,
              decoration: const InputDecoration(
                labelText: 'Language',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(
                  value: AppLanguage.system,
                  child: Text('System'),
                ),
                DropdownMenuItem(value: AppLanguage.thai, child: Text('ไทย')),
                DropdownMenuItem(
                  value: AppLanguage.english,
                  child: Text('English'),
                ),
              ],
              onChanged: (value) {
                if (value != null) controller.setLanguage(value);
              },
            ),
            const SizedBox(height: 24),
            Text('Governance', style: Theme.of(context).textTheme.titleLarge),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Require approval for high-risk actions'),
              subtitle: const Text(
                'Keep a human approval step before sensitive AI execution.',
              ),
              value: controller.requireApprovalForHighRisk,
              onChanged: controller.setRequireApprovalForHighRisk,
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Retain evidence history'),
              subtitle: const Text(
                'Keep execution evidence available for review and audit.',
              ),
              value: controller.retainEvidence,
              onChanged: controller.setRetainEvidence,
            ),
            const SizedBox(height: 24),
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                onPressed: controller.reset,
                icon: const Icon(Icons.restore),
                label: const Text('Reset settings'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
