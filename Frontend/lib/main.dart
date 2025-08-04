/// main.dart
///
/// Einstiegspunkt der Flutter-App *Digital Twin Viewer*.
///
/// * Entscheidet per `SharedPreferences`, ob **LoginScreen** oder
///   **HomeScreen** angezeigt wird.
/// * Nutzt eine 10-Minuten-Inaktivitäts-Timeout-Logik.
///
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/home_screen.dart';
import 'screens/login_screen.dart';

void main() => runApp(const MyApp());

/// Root-Widget der App.
///
/// Entscheidet asynchron, ob der Benutzer noch eingeloggt ist
/// (inkl. Timeout) und zeigt dann den passenden Start-Screen.
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // ---------------------------------------------------------------------------
  // Privater Helfer: Start-Screen ermitteln
  // ---------------------------------------------------------------------------
  Future<Widget> _determineStartScreen() async {
    final prefs = await SharedPreferences.getInstance();
    final isLoggedIn = prefs.getBool('isLoggedIn') ?? false;

    // Timeout-Logik (10 Minuten)
    const timeoutMs = 10 * 60 * 1_000;
    final lastActive = prefs.getInt('lastActive') ?? 0;
    final expired = DateTime.now().millisecondsSinceEpoch - lastActive > timeoutMs;

    return (isLoggedIn && !expired) ? const HomeScreen() : const LoginScreen();
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Digital Twin Viewer',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
          useMaterial3: true,
        ),
        home: FutureBuilder<Widget>(
          future: _determineStartScreen(),
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.done && snap.hasData) {
              return snap.data!;
            }
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          },
        ),
      );
}
