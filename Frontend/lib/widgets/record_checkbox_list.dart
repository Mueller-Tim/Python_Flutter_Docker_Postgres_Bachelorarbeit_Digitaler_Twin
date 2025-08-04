/// record_checkbox_list.dart
///
/// Listet alle verfügbaren Attribute (DNS-Records, Subdomains, …) als
/// vertikale Checkboxen auf.  Jede Checkbox hat ein kleines **Info-Icon**,
/// das per Dialog die Plugin-Beschreibung und Spaltenüberschriften anzeigt.
///
/// * Die Auswahl wird via [onChanged] an den aufrufenden Screen gemeldet.
/// * Die Beschreibungen kommen asynchron über [`pluginRegistry`].
///
import 'package:flutter/material.dart';

import '../services/plugin_registry.dart';

/// Checkbox-Liste für Attribut-Auswahl inkl. Info-Dialog.
class RecordCheckboxList extends StatelessWidget {
  const RecordCheckboxList({
    super.key,
    required this.recordSelections,
    required this.onChanged,
  });

  /// Aktueller Checkbox-Status (Anzeige-Name → checked).
  final Map<String, bool> recordSelections;

  /// Callback bei Änderung einer Checkbox.
  final void Function(String key, bool isChecked) onChanged;

  // ---------------------------------------------------------------------------
  // Private Hilfs­methode: Plugin-Info-Dialog
  // ---------------------------------------------------------------------------
  Future<void> _showPluginInfo(BuildContext context, String key) async {
    final plugin = pluginRegistry[key];
    if (plugin == null) return;

    final info = await plugin.describe();
    final title = info['name'] ?? key;
    final desc = info['Beschreibung'] ?? 'Keine Beschreibung verfügbar.';
    final cols = (info['columns'] as List?)?.join('\n• ') ?? '';

    if (!context.mounted) return;
    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(title),
        content: Text('$desc\n\n📄 Spalten:\n• $cols'),
        actions: [
          TextButton(
            onPressed: Navigator.of(context).pop,
            child: const Text('Schließen'),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) => Column(
        children: recordSelections.entries.map((e) {
          return CheckboxListTile(
            value: e.value,
            onChanged: (val) => onChanged(e.key, val ?? false),
            title: Row(
              children: [
                Expanded(child: Text(e.key)),
                IconButton(
                  icon: const Icon(Icons.info_outline, size: 18),
                  tooltip: 'Info anzeigen',
                  onPressed: () => _showPluginInfo(context, e.key),
                ),
              ],
            ),
          );
        }).toList(),
      );
}
