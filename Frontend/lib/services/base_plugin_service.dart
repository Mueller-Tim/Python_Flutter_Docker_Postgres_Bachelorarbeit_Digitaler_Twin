/// base_plugin_service.dart
///
/// Stellt HTTP-Helper für alle Plugin-Services bereit:
/// * `scan()`       – löst einen Live-Scan beim Backend aus
/// * `getValues()`  – holt persistierte Daten aus der DB
/// * `describe()`   – liest Metadaten (Name, Spalten, …)
///
/// ```text
///   GET /scan?attribute=A&domain=example.com
///   GET /get?attribute=A&domain=example.com
///   GET /describe?attribute=A
/// ```
///
import 'dart:convert';

import 'package:http/http.dart' as http;

/// Gemeinsame Service-Basisklasse für alle Plugins.
class BasePluginService {
  /// Attribut-Schlüssel (z. B. `A`, `MX`, `subdomain`).
  final String attribute;

  /// Basis-URL deines Backends.
  static const _base = 'http://localhost:8000';

  const BasePluginService(this.attribute);

  // ---------------------------------------------------------------------------
  // Scan
  // ---------------------------------------------------------------------------
  /// Triggert einen Live-Scan für [domain].
  ///
  /// Gibt eine Status- oder Fehlermeldung zurück.
  Future<String> scan(String domain) async {
    final uri = Uri.parse('$_base/scan?attribute=$attribute&domain=$domain');

    try {
      final res = await http.get(uri);
      final decoded = utf8.decode(res.bodyBytes);
      final json = jsonDecode(decoded) as Map<String, dynamic>;
      return json['error'] ?? json['status'] ?? '⚠️ Keine Antwort';
    } catch (e) {
      return '❌ Fehler bei Scan ($attribute): $e';
    }
  }

  // ---------------------------------------------------------------------------
  // Persistierte Daten abrufen
  // ---------------------------------------------------------------------------
  /// Lädt gespeicherte Werte für [domain].
  ///
  /// Liefert stets eine Liste (auch bei nur einem Objekt oder Error).
  Future<List<dynamic>> getValues(String domain) async {
    final uri = Uri.parse('$_base/get?attribute=$attribute&domain=$domain');

    try {
      final res = await http.get(uri);
      final decoded = utf8.decode(res.bodyBytes);
      final json = jsonDecode(decoded);
      return json is List ? json : [json];
    } catch (e) {
      return [
        {'error': '❌ Fehler beim Abrufen ($attribute): $e'}
      ];
    }
  }

  // ---------------------------------------------------------------------------
  // Metadaten
  // ---------------------------------------------------------------------------
  /// Ruft Plugin-Metadaten (Name, Beschreibung, Columns) ab.
  Future<Map<String, dynamic>> describe() async {
    final uri = Uri.parse('$_base/describe?attribute=$attribute');

    try {
      final res = await http.get(uri);
      if (res.statusCode == 200) {
        final decoded = utf8.decode(res.bodyBytes);
        final json = jsonDecode(decoded);
        return json is Map<String, dynamic> ? json : {};
      } else {
        return {'error': 'Serverfehler ${res.statusCode}'};
      }
    } catch (e) {
      return {'error': '❌ Fehler beim Laden der Beschreibung: $e'};
    }
  }
}
