enum AiPrivacyLevel {
  localOnly,
  organizationInternal,
  approvedCloud,
  externalCloud,
  restricted,
}

enum AiRiskLevel { low, medium, high, critical }

class AiExecutionContext {
  const AiExecutionContext({
    required this.privacyLevel,
    required this.riskLevel,
    this.containsSensitiveData = false,
    this.requiresTools = false,
  });

  final AiPrivacyLevel privacyLevel;
  final AiRiskLevel riskLevel;
  final bool containsSensitiveData;
  final bool requiresTools;
}

class AiPolicyDecision {
  const AiPolicyDecision._({
    required this.allowed,
    required this.requiresApproval,
    required this.reason,
  });

  const AiPolicyDecision.allow({bool requiresApproval = false})
    : this._(allowed: true, requiresApproval: requiresApproval, reason: null);

  const AiPolicyDecision.deny(String reason)
    : this._(allowed: false, requiresApproval: false, reason: reason);

  final bool allowed;
  final bool requiresApproval;
  final String? reason;
}

class AiExecutionPolicy {
  const AiExecutionPolicy({
    this.requireApprovalForHighRisk = true,
    this.highRiskApprovalRequired,
  });

  final bool requireApprovalForHighRisk;
  final bool Function()? highRiskApprovalRequired;

  AiPolicyDecision evaluate(AiExecutionContext context) {
    if (context.privacyLevel == AiPrivacyLevel.restricted) {
      return const AiPolicyDecision.deny(
        'Restricted data cannot be routed to an AI provider.',
      );
    }

    if (context.containsSensitiveData &&
        context.privacyLevel != AiPrivacyLevel.localOnly &&
        context.privacyLevel != AiPrivacyLevel.organizationInternal) {
      return const AiPolicyDecision.deny(
        'Sensitive data requires local or organization-internal processing.',
      );
    }

    if (context.riskLevel == AiRiskLevel.critical) {
      return const AiPolicyDecision.deny(
        'Critical-risk AI actions are blocked by policy.',
      );
    }

    final highRiskApprovalRequired =
        this.highRiskApprovalRequired?.call() ?? requireApprovalForHighRisk;
    final approval =
        (highRiskApprovalRequired && context.riskLevel == AiRiskLevel.high) ||
        context.requiresTools ||
        context.privacyLevel == AiPrivacyLevel.externalCloud;

    return AiPolicyDecision.allow(requiresApproval: approval);
  }
}
