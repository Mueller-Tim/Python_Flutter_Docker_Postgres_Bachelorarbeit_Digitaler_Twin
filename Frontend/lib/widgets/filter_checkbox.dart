/// filter_checkbox.dart
///
/// Horizontale Scroll-Leiste mit Checkboxen, um bereits geladene
/// Ergebnis-Attribute ein- oder auszublenden.
///
/// Die Komponente ist bewusst **stateless**; den Zustand (`filterSelections`)
/// verwaltet der aufrufende Screen.
///
import 'package:flutter/material.dart';

/// Checkbox-Leiste zum Filtern angezeigter Attribute.
///
/// * [filterSelections] – Map *Attribut → bool* (checked/un-checked)
/// * [onChanged] – Callback, das bei jeder Änderung `(key, value)` feuert
class FilterCheckbox extends StatelessWidget {
  const FilterCheckbox({
    super.key,
    required this.filterSelections,
    required this.onChanged,
  });

  /// Aktueller Checkbox-Status.
  final Map<String, bool> filterSelections;

  /// Callback bei Änderung einer Checkbox.
  final void Function(String key, bool value) onChanged;

  @override
  Widget build(BuildContext context) => SizedBox(
        height: 60, // etwas Platz für CheckboxListTile
        child: ListView(
          scrollDirection: Axis.horizontal,
          children: filterSelections.entries.map((e) {
            return Container(
              constraints: const BoxConstraints(minWidth: 50, maxWidth: 180),
              margin: const EdgeInsets.symmetric(horizontal: 6),
              child: CheckboxListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                title: Text(
                  e.key,
                  overflow: TextOverflow.ellipsis,
                ),
                value: e.value,
                onChanged: (val) => onChanged(e.key, val ?? false),
              ),
            );
          }).toList(),
        ),
      );
}
