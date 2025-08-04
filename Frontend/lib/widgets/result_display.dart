/// result_display.dart
///
/// Universelles Widget zur Darstellung von Plugin-Ergebnissen.
///
/// * Erkennt automatisch JSON-Strings (`Map` / `List<Map>`)
/// * Zeigt Tabellen in einer **scrollbaren** [`JsonTable`] an
/// * Gibt reine Strings (oder Error/Info-Meldungen) als monospace-Text aus
///
/// Umgang mit Spezialfällen
/// ------------------------
/// * `[{ "info": "…" }]`   → grüne Info-Textzeile
/// * `[{ "error": "…" }]`  → rote Fehler-Textzeile
///
import 'dart:convert';

import 'package:flutter/material.dart';

import 'json_table.dart';

/// Darstellung eines JSON- oder Plain-Text-Ergebnisses.
class ResultDisplay extends StatelessWidget {
  const ResultDisplay({
    super.key,
    required this.text,
  });

  /// Rohtext (meist JSON-String) eines Plugin-Calls.
  final String text;

  @override
  Widget build(BuildContext context) {
    // Max. 80 % der Bildschirmhöhe für Tabellen nutzen
    final maxTableHeight = MediaQuery.of(context).size.height * 0.8;

    // -----------------------------------------------------------------------
    // 1) JSON parsen
    // -----------------------------------------------------------------------
    dynamic parsed;
    try {
      parsed = jsonDecode(text);
    } catch (_) {
      // Nicht-JSON → direkt als Plain-Text darstellen
      return _asText(text);
    }

    // -----------------------------------------------------------------------
    // 2) Sonderfall: Einzelne Info-/Error-Map
    // -----------------------------------------------------------------------
    if (parsed is List &&
        parsed.length == 1 &&
        parsed.first is Map<String, dynamic>) {
      final map = parsed.first as Map<String, dynamic>;
      if (map.containsKey('info')) {
        return _asText(map['info'].toString());
      } else if (map.containsKey('error')) {
        return _asText(map['error'].toString(), isError: true);
      }
    }

    // -----------------------------------------------------------------------
    // 3) Normale Tabelle (List<Map<String,dynamic>>)
    // -----------------------------------------------------------------------
    if (parsed is List &&
        parsed.isNotEmpty &&
        parsed.first is Map<String, dynamic>) {
      return JsonTable(
        data: List<Map<String, dynamic>>.from(parsed),
        maxHeight: maxTableHeight,
      );
    }

    // -----------------------------------------------------------------------
    // 4) Fallback – Plain-Text
    // -----------------------------------------------------------------------
    return _asText(text);
  }

  // -------------------------------------------------------------------------
  // Helper: Plain-Text in monospace
  // -------------------------------------------------------------------------
  Widget _asText(String value, {bool isError = false}) => SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Text(
          value,
          style: TextStyle(
            fontFamily: 'monospace',
            color: isError ? Colors.red : Colors.black,
          ),
        ),
      );
}
