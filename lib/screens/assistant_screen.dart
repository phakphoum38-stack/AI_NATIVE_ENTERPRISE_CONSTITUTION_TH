import 'package:flutter/material.dart';

import '../ai_engine/session/ai_session_controller.dart';
import '../core/policy/ai_policy.dart';

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({required this.controller, super.key});

  final AiSessionController controller;

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final TextEditingController _promptController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _promptController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.controller,
      builder: (context, _) {
        final decision = widget.controller.evaluateCurrentPolicy();
        return Column(
          children: [
            _PolicyBar(controller: widget.controller, decision: decision),
            const Divider(height: 1),
            Expanded(
              child: widget.controller.messages.isEmpty
                  ? const _EmptyConversation()
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(20),
                      itemCount: widget.controller.messages.length,
                      itemBuilder: (context, index) {
                        return _MessageCard(
                          message: widget.controller.messages[index],
                        );
                      },
                    ),
            ),
            if (widget.controller.errorMessage case final error?)
              MaterialBanner(
                content: Text(error),
                actions: [
                  TextButton(
                    onPressed: widget.controller.clearConversation,
                    child: const Text('ล้าง'),
                  ),
                ],
              ),
            _Composer(
              promptController: _promptController,
              isSending: widget.controller.isSending,
              canSend: decision.allowed,
              requiresApproval: decision.requiresApproval,
              onSend: _send,
              onCancel: widget.controller.cancel,
            ),
          ],
        );
      },
    );
  }

  Future<void> _send(bool approved) async {
    final text = _promptController.text;
    if (text.trim().isEmpty) return;
    _promptController.clear();

    try {
      await widget.controller.send(text, approved: approved);
      if (!mounted) return;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250),
            curve: Curves.easeOut,
          );
        }
      });
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('คำขอถูกปฏิเสธหรือส่งไม่สำเร็จ')),
      );
    }
  }
}

class _PolicyBar extends StatelessWidget {
  const _PolicyBar({required this.controller, required this.decision});

  final AiSessionController controller;
  final AiPolicyDecision decision;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          DropdownButton<AiPrivacyLevel>(
            value: controller.privacyLevel,
            onChanged: (value) {
              if (value != null) controller.setPrivacyLevel(value);
            },
            items: [
              for (final value in AiPrivacyLevel.values)
                DropdownMenuItem(value: value, child: Text(value.name)),
            ],
          ),
          const SizedBox(width: 16),
          DropdownButton<AiRiskLevel>(
            value: controller.riskLevel,
            onChanged: (value) {
              if (value != null) controller.setRiskLevel(value);
            },
            items: [
              for (final value in AiRiskLevel.values)
                DropdownMenuItem(value: value, child: Text(value.name)),
            ],
          ),
          const SizedBox(width: 16),
          FilterChip(
            label: const Text('Sensitive data'),
            selected: controller.containsSensitiveData,
            onSelected: controller.setContainsSensitiveData,
          ),
          const SizedBox(width: 8),
          FilterChip(
            label: const Text('Requires tools'),
            selected: controller.requiresTools,
            onSelected: controller.setRequiresTools,
          ),
          const SizedBox(width: 16),
          Chip(
            avatar: Icon(
              decision.allowed ? Icons.verified_user : Icons.block,
              size: 18,
            ),
            label: Text(
              decision.allowed
                  ? decision.requiresApproval
                      ? 'Allowed with approval'
                      : 'Allowed'
                  : 'Blocked',
            ),
          ),
        ],
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.promptController,
    required this.isSending,
    required this.canSend,
    required this.requiresApproval,
    required this.onSend,
    required this.onCancel,
  });

  final TextEditingController promptController;
  final bool isSending;
  final bool canSend;
  final bool requiresApproval;
  final ValueChanged<bool> onSend;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: promptController,
                minLines: 1,
                maxLines: 5,
                enabled: !isSending,
                decoration: const InputDecoration(
                  hintText: 'พิมพ์คำสั่งหรือคำถาม...',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 12),
            if (isSending)
              IconButton.filledTonal(
                onPressed: onCancel,
                icon: const Icon(Icons.stop),
                tooltip: 'ยกเลิก',
              )
            else
              FilledButton.icon(
                onPressed: canSend
                    ? () => onSend(requiresApproval)
                    : null,
                icon: Icon(
                  requiresApproval ? Icons.approval_outlined : Icons.send,
                ),
                label: Text(requiresApproval ? 'อนุมัติและส่ง' : 'ส่ง'),
              ),
          ],
        ),
      ),
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({required this.message});

  final AiConversationMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760),
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isUser ? 'User' : 'AI',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 8),
                SelectableText(message.text),
                if (message.providerId != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    '${message.providerId} · ${message.model}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EmptyConversation extends StatelessWidget {
  const _EmptyConversation();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Text(
          'เลือก Provider แล้วเริ่มสนทนา\nทุกคำขอจะผ่าน Policy และถูกบันทึก Evidence',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
