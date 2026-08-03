import 'package:ai_native_enterprise_constitution/app/app_settings.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('settings controller updates and resets preferences', () {
    final controller = AppSettingsController();
    var notifications = 0;
    controller.addListener(() => notifications++);

    controller.setThemeMode(ThemeMode.dark);
    controller.setLanguage(AppLanguage.thai);
    controller.setRequireApprovalForHighRisk(false);
    controller.setRetainEvidence(false);

    expect(controller.themeMode, ThemeMode.dark);
    expect(controller.locale, const Locale('th'));
    expect(controller.requireApprovalForHighRisk, isFalse);
    expect(controller.retainEvidence, isFalse);
    expect(notifications, 4);

    controller.reset();

    expect(controller.themeMode, ThemeMode.system);
    expect(controller.language, AppLanguage.system);
    expect(controller.locale, isNull);
    expect(controller.requireApprovalForHighRisk, isTrue);
    expect(controller.retainEvidence, isTrue);
  });
}
