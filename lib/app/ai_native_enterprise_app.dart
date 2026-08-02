import 'package:flutter/material.dart';

import '../screens/app_shell.dart';
import 'app_dependencies.dart';

class AiNativeEnterpriseApp extends StatelessWidget {
  const AiNativeEnterpriseApp({required this.dependencies, super.key});

  final AppDependencies dependencies;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Native Enterprise Constitution',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: AppShell(dependencies: dependencies),
    );
  }
}
