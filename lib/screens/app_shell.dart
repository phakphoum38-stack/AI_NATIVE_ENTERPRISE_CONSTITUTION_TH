import 'package:flutter/material.dart';

import '../app/app_dependencies.dart';
import 'assistant_screen.dart';
import 'evidence_screen.dart';
import 'home_screen.dart';

class AppShell extends StatefulWidget {
  const AppShell({required this.dependencies, super.key});

  final AppDependencies dependencies;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 900;
    final destinations = const <NavigationRailDestination>[
      NavigationRailDestination(
        icon: Icon(Icons.dashboard_outlined),
        selectedIcon: Icon(Icons.dashboard),
        label: Text('Dashboard'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.auto_awesome_outlined),
        selectedIcon: Icon(Icons.auto_awesome),
        label: Text('Assistant'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.fact_check_outlined),
        selectedIcon: Icon(Icons.fact_check),
        label: Text('Evidence'),
      ),
    ];

    final body = IndexedStack(
      index: _selectedIndex,
      children: [
        HomeScreen(controller: widget.dependencies.aiProviderController),
        AssistantScreen(controller: widget.dependencies.aiSessionController),
        EvidenceScreen(evidenceLog: widget.dependencies.evidenceLog),
      ],
    );

    return Scaffold(
      body: wide
          ? Row(
              children: [
                NavigationRail(
                  selectedIndex: _selectedIndex,
                  onDestinationSelected: _select,
                  labelType: NavigationRailLabelType.all,
                  leading: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 16),
                    child: CircleAvatar(
                      child: Icon(Icons.account_tree_outlined),
                    ),
                  ),
                  destinations: destinations,
                ),
                const VerticalDivider(width: 1),
                Expanded(child: body),
              ],
            )
          : body,
      bottomNavigationBar: wide
          ? null
          : NavigationBar(
              selectedIndex: _selectedIndex,
              onDestinationSelected: _select,
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.dashboard_outlined),
                  selectedIcon: Icon(Icons.dashboard),
                  label: 'Dashboard',
                ),
                NavigationDestination(
                  icon: Icon(Icons.auto_awesome_outlined),
                  selectedIcon: Icon(Icons.auto_awesome),
                  label: 'Assistant',
                ),
                NavigationDestination(
                  icon: Icon(Icons.fact_check_outlined),
                  selectedIcon: Icon(Icons.fact_check),
                  label: 'Evidence',
                ),
              ],
            ),
    );
  }

  void _select(int value) {
    setState(() => _selectedIndex = value);
  }
}
