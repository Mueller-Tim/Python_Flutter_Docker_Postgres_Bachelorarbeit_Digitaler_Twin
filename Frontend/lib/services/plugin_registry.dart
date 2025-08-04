/// plugin_registry.dart
///
/// Enthält eine zentrale Zuordnung **Anzeige-Bezeichnung ⇢ Plugin-Service**.
///
/// Auf diese Weise kann die UI ein Attribut wie *„A-Record“* auswählen
/// und bekommt über `pluginRegistry['A-Record']` direkt die passende
/// [`BasePluginService`]-Instanz.
///
/// Nutzt **`BasePluginService(attribute)`** als dünne Wrapper-Klasse für
/// alle HTTP-Aufrufe (*/scan*, */get*, */describe*).
///
import 'base_plugin_service.dart';

/// Bequemer Getter – nimmt Groß-/Kleinschreibung nicht so ernst.
///
/// Beispiel
/// ```dart
/// final srv = getPlugin('mx-record');
/// await srv?.scan('example.com');
/// ```
BasePluginService? getPlugin(String key) =>
    pluginRegistry[key] ?? pluginRegistry[key.toUpperCase()] ?? pluginRegistry[key.toLowerCase()];

/// Registry aller verfügbaren Plugin-Services.
///
/// *Schlüssel* = Anzeige-Name in der UI
/// *Wert*      = [`BasePluginService`] mit dem Core-Attribut-Key
final Map<String, BasePluginService> pluginRegistry = {
  // DNS-Records
  'A-Record': BasePluginService('A'),
  'AAAA-Record': BasePluginService('AAAA'),
  'MX-Record': BasePluginService('MX'),
  'NS-Record': BasePluginService('NS'),
  'TXT-Record': BasePluginService('TXT'),
  'SOA-Record': BasePluginService('SOA'),
  'PTR-Record': BasePluginService('PTR'),

  // Weitere Teil-Scanner
  'Subdomain': BasePluginService('subdomain'),
  'Zertifikat': BasePluginService('certificate'),
  'Endpunkt': BasePluginService('endpoint'),
  'E-Mail': BasePluginService('email'),
  'Telefonnummer': BasePluginService('phone'),
  'Dienst': BasePluginService('service'),
};
