import 'package:ai_native_enterprise_constitution/core/maturity/enterprise_maturity.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const evaluator = EnterpriseMaturityEvaluator();

  test('defaults to prototype when foundation criteria are incomplete', () {
    final assessment = evaluator.evaluate(
      const EnterpriseCapabilities(hasRunnableFeature: true),
    );

    expect(assessment.level, EnterpriseMaturityLevel.prototype);
    expect(assessment.isEnterpriseReady, isFalse);
    expect(assessment.metCriteria, contains('Runnable feature'));
    expect(assessment.missingCriteria, contains('Architecture documentation'));
  });

  test('reaches structured when architecture tests and CI are present', () {
    final assessment = evaluator.evaluate(
      const EnterpriseCapabilities(
        hasRunnableFeature: true,
        hasArchitectureDocumentation: true,
        hasAutomatedTests: true,
        hasContinuousIntegration: true,
      ),
    );

    expect(assessment.level, EnterpriseMaturityLevel.structured);
    expect(assessment.isEnterpriseReady, isFalse);
  });

  test('reaches enterprise only when every enterprise control is present', () {
    final assessment = evaluator.evaluate(
      const EnterpriseCapabilities(
        hasRunnableFeature: true,
        hasArchitectureDocumentation: true,
        hasAutomatedTests: true,
        hasContinuousIntegration: true,
        hasContinuousDelivery: true,
        hasDecisionRecords: true,
        hasSecurityControls: true,
        hasObservability: true,
        hasPluginBoundary: true,
        hasSeds: true,
      ),
    );

    expect(assessment.level, EnterpriseMaturityLevel.enterprise);
    expect(assessment.isEnterpriseReady, isTrue);
    expect(assessment.missingCriteria, isEmpty);
  });
}
