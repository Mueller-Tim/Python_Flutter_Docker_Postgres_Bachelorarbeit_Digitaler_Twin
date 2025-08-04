import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../services/plugin_registry.dart';
import '../widgets/filter_checkbox.dart';
import '../widgets/record_checkbox_list.dart';
import '../widgets/result_display.dart';
import 'login_screen.dart';

/// Start-Screen des »Digitalen Twin«-Scanners.
///
/// * Eingabe einer Domain
/// * Auswahl der Attribute (A-Record, Subdomain …)
/// * Buttons: **Scan**, **Anzeigen**, **Exportieren**
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

/// `State`-Klasse – hält UI-Zustand & ruft Plugins auf.
class _HomeScreenState extends State<HomeScreen> {
  // ---------------------------------------------------------------------------
  // Controller & Auswahldaten
  // ---------------------------------------------------------------------------
  final _domainCtl = TextEditingController();

  /// Checkbox-Status pro Attribut.
  final Map<String, bool> _recordSelections = {
    'A-Record': false,
    'AAAA-Record': false,
    'MX-Record': false,
    'NS-Record': false,
    'TXT-Record': false,
    'SOA-Record': false,
    'PTR-Record': false,
    'Subdomain': false,
    'Zertifikat': false,
    'Endpunkt': false,
    'E-Mail': false,
    'Telefonnummer': false,
    'Dienst': false,
  };

  /// Daraus generierter Filter (nur aktiv gewählte).
  Map<String, bool> _filterSelections = {};

  final _plugins = pluginRegistry;
  bool _allSelected = false;

  /// Ergebnisse aus `get`-Aufrufen je Attribut.
  Map<String, List<dynamic>> _responseMap = {};

  /// Status aus `scan`-Aufrufen je Attribut (Error / Info).
  Map<String, dynamic> _scanStatusMap = {};

  bool _isLoading = false;

  // ---------------------------------------------------------------------------
  // Convenience-Methoden
  // ---------------------------------------------------------------------------

  /// Toggle »Alle auswählen«-Checkbox.
  void _toggleAll(bool? value) {
    setState(() {
      _allSelected = value ?? false;
      _recordSelections.updateAll((_, __) => _allSelected);
    });
  }

  /// Zeigt während eines Futures einen `CircularProgressIndicator`.
  Future<void> _withLoading(Future<void> Function() action) async {
    setState(() => _isLoading = true);
    try {
      await action();
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  // ---------------------------------------------------------------------------
  // Plugin-Aktionen
  // ---------------------------------------------------------------------------

  Future<void> _scan() async => _withLoading(() async {
        final domain = _domainCtl.text.trim();
        if (domain.isEmpty) return;

        _filterSelections = Map.fromEntries(
          _recordSelections.entries.where((e) => e.value),
        );

        final statusMap = <String, dynamic>{};

        for (final entry in _filterSelections.entries) {
          final plugin = _plugins[entry.key];
          if (plugin == null) continue;

          final status = await plugin.scan(domain);
          final isError =
              status.startsWith('❌') || status.contains('Fehler') || status.contains('error');
          statusMap[entry.key] = {isError ? 'error' : 'info': status};
        }

        if (mounted) setState(() => _scanStatusMap = statusMap);
      });

  Future<void> _getAndDisplay() async => _withLoading(() async {
        final domain = _domainCtl.text.trim();
        if (domain.isEmpty) return;

        final active = _recordSelections.entries
            .where((e) => e.value)
            .map((e) => e.key);

        final Map<String, List<dynamic>> res = {};
        for (final key in active) {
          final plugin = _plugins[key];
          if (plugin != null) res[key] = await plugin.getValues(domain);
        }

        if (mounted) setState(() => _responseMap = res);
      });

  Future<void> _export() async {
    final domain = _domainCtl.text.trim();
    if (domain.isEmpty) return;

    final active = _recordSelections.entries.where((e) => e.value).map((e) => e.key);

    if (active.isEmpty) {
      _showSnack('⚠️ Keine Attribute ausgewählt');
      return;
    }

    final Map<String, dynamic> res = {};
    for (final key in active) {
      final plugin = _plugins[key];
      if (plugin != null) res[key] = await plugin.getValues(domain);
    }

    if (res.isEmpty) {
      _showSnack('❌ Keine Daten zum Exportieren gefunden');
      return;
    }

    await ApiService.exportJson(domain, res, pretty: true);
    _showSnack('📦 JSON erfolgreich exportiert');
  }

  // ---------------------------------------------------------------------------
  // UI-Helfer
  // ---------------------------------------------------------------------------

  void _showSnack(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Digitaler Twin'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Abmelden',
            onPressed: _logout,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _DomainInput(controller: _domainCtl),
            const SizedBox(height: 20),
            CheckboxListTile(
              title: const Text('Alle auswählen'),
              value: _allSelected,
              onChanged: _toggleAll,
            ),
            const SizedBox(height: 10),
            RecordCheckboxList(
              recordSelections: _recordSelections,
              onChanged: (key, val) {
                setState(() {
                  _recordSelections[key] = val;
                  _allSelected = _recordSelections.values.every((v) => v);
                });
              },
            ),
            const SizedBox(height: 10),
            _ActionButtons(
              isLoading: _isLoading,
              onScan: _scan,
              onShow: _getAndDisplay,
              onExport: _export,
            ),
            const SizedBox(height: 20),
            FilterCheckbox(
              filterSelections: _filterSelections,
              onChanged: (k, v) {
                setState(() {
                  _filterSelections[k] = v;
                  _getAndDisplay(); // sofort aktualisieren
                });
              },
            ),
            const SizedBox(height: 20),
            if (_scanStatusMap.isNotEmpty) _ScanStatus(statusMap: _scanStatusMap),
            if (_isLoading) const Center(child: CircularProgressIndicator()),
            const SizedBox(height: 20),
            const Text('Ergebnisse:', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            if (_responseMap.isNotEmpty) _ResultList(responseMap: _responseMap),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// Kleine, private Helper-Widgets
// ============================================================================

class _DomainInput extends StatelessWidget {
  const _DomainInput({required this.controller});
  final TextEditingController controller;

  @override
  Widget build(BuildContext context) => TextField(
        controller: controller,
        decoration: const InputDecoration(
          labelText: 'Domain (z.B. example.com)',
          border: OutlineInputBorder(),
        ),
      );
}

class _ActionButtons extends StatelessWidget {
  const _ActionButtons({
    required this.isLoading,
    required this.onScan,
    required this.onShow,
    required this.onExport,
  });

  final bool isLoading;
  final VoidCallback onScan, onShow, onExport;

  @override
  Widget build(BuildContext context) => Row(
        children: [
          ElevatedButton(
            onPressed: isLoading ? null : onScan,
            child: const Text('Scan starten'),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: ElevatedButton(
              onPressed: isLoading ? null : onShow,
              child: const Text('Anzeigen'),
            ),
          ),
          const SizedBox(width: 10),
          ElevatedButton(
            onPressed: isLoading ? null : onExport,
            child: const Text('Exportieren'),
          ),
        ],
      );
}

class _ScanStatus extends StatelessWidget {
  const _ScanStatus({required this.statusMap});
  final Map<String, dynamic> statusMap;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: statusMap.entries.map((e) {
          final isError = e.value.containsKey('error');
          final txt = e.value[isError ? 'error' : 'info'];
          return Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              '🔍 ${e.key}: $txt',
              style: TextStyle(
                color: isError ? Colors.red : Colors.green,
                fontWeight: FontWeight.w500,
              ),
            ),
          );
        }).toList(),
      );
}

class _ResultList extends StatelessWidget {
  const _ResultList({required this.responseMap});
  final Map<String, List<dynamic>> responseMap;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: responseMap.entries.map((e) {
          final prettyJson = const JsonEncoder.withIndent('  ').convert(e.value);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('📄 ${e.key}:',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 5),
              ResultDisplay(text: prettyJson),
              const SizedBox(height: 20),
            ],
          );
        }).toList(),
      );
}
