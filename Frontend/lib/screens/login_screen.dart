import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'home_screen.dart';

/// Login-Screen für den *Digitalen Twin*.
///
/// * Holt das Admin-Passwort beim Start vom Backend
/// * Prüft Benutzername + Passwort
/// * Speichert Login-Status in `SharedPreferences`
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  // ---------------------------------------------------------------------------
  // Controller & State-Variablen
  // ---------------------------------------------------------------------------
  final _userCtl = TextEditingController();
  final _passCtl = TextEditingController();

  bool _isLoadingPw = true;
  String? _error;

  static const _validUser = 'admin';
  String? _validPassword;

  // ---------------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------------
  @override
  void initState() {
    super.initState();
    _fetchPassword();
  }

  // ---------------------------------------------------------------------------
  // Netzwerk / Persistence
  // ---------------------------------------------------------------------------
  Future<void> _fetchPassword() async {
    const url = 'http://localhost:8000/api/admin-password';
    try {
      final res = await http.get(Uri.parse(url));
      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        setState(() => _validPassword = data['password'] as String?);
      } else {
        setState(() => _error = '⚠️ Passwort konnte nicht geladen werden');
      }
    } catch (e) {
      setState(() => _error = '❌ Netzwerkfehler: $e');
    } finally {
      setState(() => _isLoadingPw = false);
    }
  }

  Future<void> _saveLogin() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs
      ..setBool('isLoggedIn', true)
      ..setInt('lastActive', DateTime.now().millisecondsSinceEpoch);
  }

  // ---------------------------------------------------------------------------
  // UI-Callbacks
  // ---------------------------------------------------------------------------
  Future<void> _login() async {
    final user = _userCtl.text.trim();
    final pass = _passCtl.text;

    if (user == _validUser && pass == _validPassword) {
      await _saveLogin();
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    } else {
      setState(() => _error = '❌ Falscher Benutzername oder Passwort');
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Digitaler Twin • Login')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            TextField(
              controller: _userCtl,
              decoration: const InputDecoration(labelText: 'Benutzername'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _passCtl,
              decoration: const InputDecoration(labelText: 'Passwort'),
              obscureText: true,
            ),
            const SizedBox(height: 20),

            // Login-Button (gesperrt bis Passwort geladen)
            ElevatedButton(
              onPressed: _isLoadingPw ? null : _login,
              child: _isLoadingPw
                  ? const SizedBox(
                      width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Anmelden'),
            ),

            // Fehlermeldung
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
          ],
        ),
      ),
    );
  }
}
