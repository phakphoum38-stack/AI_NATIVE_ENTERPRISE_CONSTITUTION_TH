import 'package:flutter/material.dart';

import '../core/evidence/evidence_log.dart';

class EvidenceScreen extends StatelessWidget {
  const EvidenceScreen({required this.evidenceLog, super.key});

  final AiEvidenceLog evidenceLog;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: evidenceLog,
      builder: (context, _) {
        final records = evidenceLog.records;
        if (records.isEmpty) {
          return const Center(
            child: Text('ยังไม่มี Evidence Record'),
          );
        }

        return Column(
          children: [
            Align(
              alignment: Alignment.centerRight,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: TextButton.icon(
                  onPressed: evidenceLog.clear,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('ล้างประวัติ'),
                ),
              ),
            ),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                itemCount: records.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final record = records[index];
                  final success = record.result == 'success';
                  return Card(
                    child: ExpansionTile(
                      leading: Icon(
                        success ? Icons.check_circle : Icons.error,
                      ),
                      title: Text(record.action),
                      subtitle: Text(
                        '${record.providerId} · ${record.model} · ${record.timestamp.toLocal()}',
                      ),
                      trailing: Chip(label: Text(record.result)),
                      childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      children: [
                        Align(
                          alignment: Alignment.centerLeft,
                          child: SelectableText(
                            record.details.entries
                                .map((entry) => '${entry.key}: ${entry.value}')
                                .join('\n'),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        );
      },
    );
  }
}
