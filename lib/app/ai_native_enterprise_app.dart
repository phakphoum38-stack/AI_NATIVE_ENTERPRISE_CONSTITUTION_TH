import 'package:flutter/material.dart';

import '../screens/app_shell.dart';
import 'app_dependencies.dart';

class AiNativeEnterpriseApp extends StatelessWidget {
  const AiNativeEnterpriseApp({required this.dependencies, super.key});

  final AppDependencies dependencies;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: dependencies.settingsController,
      builder: (context, _) {
        final settings = dependencies.settingsController;
        return MaterialApp(
          title: 'AI Native Enterprise Constitution',
          debugShowCheckedModeBanner: false,
          themeMode: settings.themeMode,
          locale: settings.locale,
          supportedLocales: const [Locale('th'), Locale('en')],
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
            useMaterial3: true,
            visualDensity: settings.compactMode
                ? VisualDensity.compact
                : VisualDensity.standard,
          ),
          darkTheme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: Colors.indigo,
              brightness: Brightness.dark,
            ),
            useMaterial3: true,
            visualDensity: settings.compactMode
                ? VisualDensity.compact
                : VisualDensity.standard,
          ),
          home: AppShell(dependencies: dependencies),
        );
      },
    );
  }
}
