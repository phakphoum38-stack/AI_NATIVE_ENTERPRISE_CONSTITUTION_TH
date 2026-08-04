import 'dart:io';

/// Formats every Dart file in the repository.
///
/// Pass `--check` to fail without modifying files when formatting is needed.
Future<void> main(List<String> arguments) async {
  if (arguments.length > 1 ||
      (arguments.isNotEmpty && arguments.single != '--check')) {
    stderr.writeln('Usage: dart run tool/format_all.dart [--check]');
    exitCode = 64;
    return;
  }

  final formatArguments = <String>[
    'format',
    if (arguments.contains('--check')) ...[
      '--output=none',
      '--set-exit-if-changed',
    ],
    '.',
  ];
  final process = await Process.start('dart', formatArguments);

  await stdout.addStream(process.stdout);
  await stderr.addStream(process.stderr);
  exitCode = await process.exitCode;
}
