import 'package:flutter/material.dart';

class AppSettingsController extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;
  Locale _locale = const Locale('th');
  bool _compactMode = false;

  ThemeMode get themeMode => _themeMode;
  Locale get locale => _locale;
  bool get compactMode => _compactMode;

  void setThemeMode(ThemeMode value) {
    if (_themeMode == value) return;
    _themeMode = value;
    notifyListeners();
  }

  void setLocale(Locale value) {
    if (_locale == value) return;
    _locale = value;
    notifyListeners();
  }

  void setCompactMode(bool value) {
    if (_compactMode == value) return;
    _compactMode = value;
    notifyListeners();
  }

  void reset() {
    _themeMode = ThemeMode.system;
    _locale = const Locale('th');
    _compactMode = false;
    notifyListeners();
  }
}
