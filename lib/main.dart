import 'package:flutter/material.dart';

import 'app/ai_native_enterprise_app.dart';
import 'app/app_dependencies.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final dependencies = AppDependencies.create();
  runApp(AiNativeEnterpriseApp(dependencies: dependencies));
}
