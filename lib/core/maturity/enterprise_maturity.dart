enum EnterpriseMaturityLevel { prototype, structured, enterprise }

class EnterpriseCapabilities {
  const EnterpriseCapabilities({
    this.hasRunnableFeature = false,
    this.hasArchitectureDocumentation = false,
    this.hasAutomatedTests = false,
    this.hasContinuousIntegration = false,
    this.hasContinuousDelivery = false,
    this.hasDecisionRecords = false,
    this.hasSecurityControls = false,
    this.hasObservability = false,
    this.hasPluginBoundary = false,
    this.hasSeds = false,
  });

  final bool hasRunnableFeature;
  final bool hasArchitectureDocumentation;
  final bool hasAutomatedTests;
  final bool hasContinuousIntegration;
  final bool hasContinuousDelivery;
  final bool hasDecisionRecords;
  final bool hasSecurityControls;
  final bool hasObservability;
  final bool hasPluginBoundary;
  final bool hasSeds;
}

class EnterpriseMaturityAssessment {
  const EnterpriseMaturityAssessment({
    required this.level,
    required this.metCriteria,
    required this.missingCriteria,
  });

  final EnterpriseMaturityLevel level;
  final List<String> metCriteria;
  final List<String> missingCriteria;

  bool get isEnterpriseReady => level == EnterpriseMaturityLevel.enterprise;
}

class EnterpriseMaturityEvaluator {
  const EnterpriseMaturityEvaluator();

  EnterpriseMaturityAssessment evaluate(EnterpriseCapabilities capabilities) {
    final met = <String>[];
    final missing = <String>[];

    void check(bool value, String criterion) {
      (value ? met : missing).add(criterion);
    }

    check(capabilities.hasRunnableFeature, 'Runnable feature');
    check(
      capabilities.hasArchitectureDocumentation,
      'Architecture documentation',
    );
    check(capabilities.hasAutomatedTests, 'Automated tests');
    check(capabilities.hasContinuousIntegration, 'Continuous integration');
    check(capabilities.hasContinuousDelivery, 'Continuous delivery');
    check(capabilities.hasDecisionRecords, 'Architecture decision records');
    check(capabilities.hasSecurityControls, 'Security controls');
    check(capabilities.hasObservability, 'Observability');
    check(capabilities.hasPluginBoundary, 'Plugin boundary');
    check(capabilities.hasSeds, 'SEDS');

    final structured =
        capabilities.hasRunnableFeature &&
        capabilities.hasArchitectureDocumentation &&
        capabilities.hasAutomatedTests &&
        capabilities.hasContinuousIntegration;

    final enterprise =
        structured &&
        capabilities.hasContinuousDelivery &&
        capabilities.hasDecisionRecords &&
        capabilities.hasSecurityControls &&
        capabilities.hasObservability &&
        capabilities.hasPluginBoundary &&
        capabilities.hasSeds;

    final level = enterprise
        ? EnterpriseMaturityLevel.enterprise
        : structured
        ? EnterpriseMaturityLevel.structured
        : EnterpriseMaturityLevel.prototype;

    return EnterpriseMaturityAssessment(
      level: level,
      metCriteria: List.unmodifiable(met),
      missingCriteria: List.unmodifiable(missing),
    );
  }
}
