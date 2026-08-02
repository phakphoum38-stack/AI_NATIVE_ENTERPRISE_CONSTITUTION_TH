import 'package:flutter/material.dart';

enum AppLanguage { system, thai, english }

class AppSettingsController extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;
  AppLanguage _language = AppLanguage.system;
  bool _requireApprovalForHighRisk = true;
  bool _retainEvidence = true;

  ThemeMode get themeMode => _themeMode;
  AppLanguage get language => _language;
  bool get requireApprovalForHighRisk => _requireApprovalForHighRisk;
  bool get retainEvidence => _retainEvidence;

  Locale? get locale => switch (_language) {
    AppLanguage.system => null,
    AppLanguage.thai => const Locale('th'),
    AppLanguage.english => const Locale('en'),
  };

  void setThemeMode(ThemeMode value) {
    if (_themeMode == value) return;
    _themeMode = value;
    notifyListeners();
  }

  void setLanguage(AppLanguage value) {
    if (_language == value) return;
    _language = value;
    notifyListeners();
  }

  void setRequireApprovalForHighRisk(bool value) {
    if (_requireApprovalForHighRisk == value) return;
    _requireApprovalForHighRisk = value;
    notifyListeners();
  }

  void setRetainEvidence(bool value) {
    if (_retainEvidence == value) return;
    _retainEvidence = value;
    notifyListeners();
  }

  void reset() {
    _themeMode = ThemeMode.system;
    _language = AppLanguage.system;
    _requireApprovalForHighRisk = true;
    _retainEvidence = true;
    notifyListeners();
  }
}
