/// api_service.dart
///
/// * Bietet eine statische Methode [`exportJson`] zum Speichern eines
///   JSON-Snapshots (inkl. Plugin-Beschreibungen) als Datei.
/// * Verwendet `file_saver` für plattformübergreifende Downloads.
///
import 'dart:convert';
import 'dart:typed_data';

import 'package:file_saver/file_saver.dart';

import 'plugin_registry.dart';

/// Hilfs-Klasse für Backend-bezogene Aktionen (z. B. Datei-Export).
class ApiService {
  /// Exportiert die gelieferten [data] als JSON-Datei.
  ///
  /// * Die Map-Struktur wird um die Plugin-Beschreibung ergänzt
  ///   (`plugin.describe()`), sodass die Exportdatei selbsterklärend ist.
  /// * Endresultat: `{ "<domain>": { "<Attribut>": [ {Beschreibung: …}, … ] } }`
  ///
  /// Parameter
  /// ----------
  /// * [domain] – Ziel-Domain (Dateiname & JSON-Root-Key).
  /// * [data]   – Rohdaten, angeordnet als *Attribut → Einträge*.
  /// * [pretty] – Schreibt das JSON formatiert („schön eingerückt“),
  ///              Standard: `false`.
  static Future<void> exportJson(
    String domain,
    Map<String, dynamic> data, {
    bool pretty = false,
  }) async {
    // -----------------------------------------------------------------------
    // 1) Map um Beschreibungen anreichern
    // -----------------------------------------------------------------------
    final enriched = <String, dynamic>{};

    for (final entry in data.entries) {
      final key = entry.key;
      final values = entry.value;

      final plugin = pluginRegistry[key];
      if (plugin != null) {
        final describe = await plugin.describe();
        enriched[key] = [
          {'Beschreibung': describe['Beschreibung'] ?? 'Keine Beschreibung vorhanden.'},
          ...values as Iterable,
        ];
      } else {
        enriched[key] = values; // Fallback, falls Plugin nicht registriert
      }
    }

    // -----------------------------------------------------------------------
    // 2) JSON encodieren
    // -----------------------------------------------------------------------
    final encoder = pretty
        ? const JsonEncoder.withIndent('  ')
        : const JsonEncoder();
    final jsonString = encoder.convert({domain: enriched});
    final bytes = Uint8List.fromList(utf8.encode(jsonString));

    // -----------------------------------------------------------------------
    // 3) Datei speichern
    // -----------------------------------------------------------------------
    await FileSaver.instance.saveFile(
      name: 'digitaler_twin_$domain',
      bytes: bytes,
      ext: 'json',
      mimeType: MimeType.json,
    );
  }
}
