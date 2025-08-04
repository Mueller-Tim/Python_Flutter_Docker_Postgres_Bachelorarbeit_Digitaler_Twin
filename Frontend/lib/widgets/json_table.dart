/// json_table.dart
///
/// Zeigt eine paginierte `DataTable`, deren Spalten dynamisch aus den
/// Keys der übergebenen JSON-Maps abgeleitet werden.
///
/// * **Horizontales Scrollen** bei breiten Tabellen  
/// * **Pagination** mit fester `rowsPerPage` (10)  
/// * Maximalhöhe einstellbar über [maxHeight]
///
import 'package:flutter/material.dart';

/// Tabellarische Anzeige einer JSON-Liste.
class JsonTable extends StatefulWidget {
  const JsonTable({
    super.key,
    required this.data,
    this.maxHeight = 600,
  });

  /// Zeilen – jede Map entspricht einer Tabellenzeile.
  final List<Map<String, dynamic>> data;

  /// Max. Höhe des Tabellencontainers.
  final double maxHeight;

  @override
  State<JsonTable> createState() => _JsonTableState();
}

class _JsonTableState extends State<JsonTable> {
  // ---------------------------------------------------------------------------
  // Paging
  // ---------------------------------------------------------------------------
  static const _rowsPerPage = 10;
  int _currentPage = 0;

  // ---------------------------------------------------------------------------
  // Scroll-Controller für horizontales Scrollen
  // ---------------------------------------------------------------------------
  final _hCtrl = ScrollController();

  @override
  void dispose() {
    _hCtrl.dispose();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Text('Keine Daten vorhanden.');
    }

    // Paging-Berechnung
    final totalPages = (widget.data.length / _rowsPerPage).ceil();
    final start = _currentPage * _rowsPerPage;
    final end = (start + _rowsPerPage).clamp(0, widget.data.length);
    final pageData = widget.data.sublist(start, end);

    // Spaltenüberschriften aus erster Zeile ableiten
    final columns = widget.data.first.keys.toList();

    return Column(
      children: [
        // ----------------------------- DataTable -----------------------------
        ConstrainedBox(
          constraints: BoxConstraints(maxHeight: widget.maxHeight),
          child: Scrollbar(
            controller: _hCtrl,
            thumbVisibility: true,
            child: SingleChildScrollView(
              controller: _hCtrl,
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: [
                  for (final col in columns)
                    DataColumn(
                      label: Text(
                        '$col:',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                ],
                rows: [
                  for (final row in pageData)
                    DataRow(
                      cells: [
                        for (final col in columns)
                          DataCell(Text(row[col]?.toString() ?? '-')),
                      ],
                    ),
                ],
              ),
            ),
          ),
        ),

        const SizedBox(height: 12),

        // ----------------------------- Pagination ----------------------------
        Text('Seite ${_currentPage + 1} / $totalPages'),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: _currentPage > 0
                  ? () => setState(() => _currentPage--)
                  : null,
              child: const Text('Zurück'),
            ),
            const SizedBox(width: 12),
            ElevatedButton(
              onPressed: _currentPage < totalPages - 1
                  ? () => setState(() => _currentPage++)
                  : null,
              child: const Text('Weiter'),
            ),
          ],
        ),
      ],
    );
  }
}
