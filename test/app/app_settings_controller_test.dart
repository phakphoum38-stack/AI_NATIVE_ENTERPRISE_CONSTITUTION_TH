import 'package:ai_native_enterprise_constitution_th/app/app_settings_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AppSettingsController', () {
    test('uses safe defaults', () {
      final controller = AppSettingsController();

      expect(controller.themeMode, ThemeMode.system);
      expect(controller.locale, const Locale('th'));
      expect(controller.compactMode, isFalse);
    });

    test('updates values and notifies listeners', () {
      final controller = AppSettingsController();
      var notifications = 0;
      controller.addListener(() => notifications += 1);

      controller.setThemeMode(ThemeMode.dark);
      controller.setLocale(const Locale('en'));
      controller.setCompactMode(true);

      expect(controller.themeMode, ThemeMode.dark);
      expect(controller.locale, const Locale('en'));
      expect(controller.compactMode, isTrue);
      expect(notifications, 3);
    });

    test('reset restores defaults', () {
      final controller = AppSettingsController()
        ..setThemeMode(ThemeMode.light)
        ..setLocale(const Locale('en'))
        ..setCompactMode(true)
        ..reset();

      expect(controller.themeMode, ThemeMode.system);
      expect(controller.locale, const Locale('th'));
      expect(controller.compactMode, isFalse);
    });
  });
}
