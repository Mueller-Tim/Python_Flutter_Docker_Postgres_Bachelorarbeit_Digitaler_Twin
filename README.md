<h1 align="center"> BA_Digital_Twin_Mueller_Thavalingam für Webseite Digitaler Twin </h1> <br>

## Inhaltsverzeichnis

- [Wie man die Webseite installiert und startet](#WiemandieWebseiteinstalliertundstartet)
    - [Weitere nützliche Befehle](#WeiterenützlicheBefehle)
- [Anleitung zur Implementierung eines Attributs](#AnleitungzurImplementierungeinesAttributs)
    - [Backend](#Backend)
    - [Frontend](#Frontend)
- [Flutter aktualisieren](#Flutteraktualisieren)
- [Team](#Team)

## Wie man die Webseite installiert und startet
1. Klone das Repositorie
  1.1. sudo apt update && sudo apt install git -y
  1.2. git clone https://github.zhaw.ch/student-theses-traa/BA_Digital_Twin_Mueller_Thavalingam.git
2. Installiere Docker:
  2.1. sudo apt update && sudo apt install docker.io -y
  2.2. sudo apt install docker-compose-plugin -y
  2.3. sudo systemctl enable --now docker
3. Öffne das Projekt in deiner IDE oder Konsoledocker
4. Container starten
  4.1. compose up --build -d
5. Container neu starten für Update (ohne Datenbank zu löschen)
  5.1. docker compose down
  5.2. docker compose up --build -d
7. Alles löschen inkl. Datenbank
  7.1. docker compose down -v
8. Webseite anschauen unter http://IP-Adresse:8080/. Die IP-Adresse ist unter dem laufenden Projekt 160.85.255.184
   
### Weitere nützliche Befehle:
- Logs ansehen: docker compose logs -f
- Liste aller laufenden Container: docker ps
- Einzelnen Dienst neu starten: docker compose restart Name


## Anleitung zur Implementierung eines Attributs

Die Anleitung ist zweigeteilt: Zunächst wird das Backend und anschließend das Frontend behandelt. Beides ist nötig, um ein Attribut zu ergänzen.

### Backend
1. Zunächst muss unter dem Ordner „Plugins” ein Unterordner mit dem Namen des englischen Plug-ins erstellt werden.
2. Damit die Fast-API das richtige Plugin findet, muss dieses unter dem Skript „Plugin_Manager.py” im „Plugin_registry” registriert werden, analog zu den anderen Plugins. Die Namen im Plugin_registry sollten mit denen des dazugehörigen Pluginordners jedes Attributes mit englischem Namen übereinstimmen. Eine Ausnahme sind bisher die DNS-Records, die aber über ihr eigenes dns_plugin.py gemappt werden.
3. Jedes Plugin muss Base_Plugin.py als Superklasse initialisieren. Denn jede Klasse braucht die drei Methoden Setup, Scan und Get. Zudem muss jedes Plugin im Init-Block die drei Parameter name, description und columns definieren, welche die Methode describe im Base-Plugin fordert.
4. Der Name des Pluginscripts muss immer zuerst den englischen Namen des Plugins enthalten, gefolgt von einem Bindestrich und dem Wort „plugin”. Diese Namenkonvention ist wichtig, damit das Plugin_registry von Punkt 2 das Plugin findet.
5. Jedes Plugin sollte möglichst verschiedene Lookup-Skripte sowie Runner-Skripte aufrufen. Lookups sollen eigenen Code ausführen und Runner externen, funktionierenden GitHub-Code.
6. Wichtige Keys sollten im Backend unter dem Ordner „Keys” abgespeichert und nicht auf Github hochgeladen werden.

### Frontend
1. Im Frontend muss man keine neuen Klassen erstellen, wenn man ein Attribut hinzufügt.
2. Gehe im Ordner „screens” in die Klasse „homescreen.dart”. Dort kann man ihm einen Namen geben, der auf der Webseite angezeigt wird und daher auch einfach von Nutzenden gelesen werden können sollte. Den Namen gibt man im Map-Objekt recordSelections an. Das „False” ist relevant, damit die Checkboxen nicht automatisch ein Attribut auswählen.
3. Unter dem Ordner „service” in der Klasse „plugin_registry.dart” findet man das Map-Objekt „pluginRegistry”. Dort muss man links den Namen eintragen, der in der Klasse „homescreen.dart” verwendet wurde. Rechts sollte man den englischen Namen ergänzen, der im Backend unter dem Script Plugin_Manager.py definiert wurde.


## Flutter aktualisieren
Wenn die Abhängigkeiten in Flutter bzw. im Frontend aktualisiert wurden, muss auch Flutter aktualisiert werden.
Wechsle in den Frontend-Ordner und führe in der CMD „flutter pub get” aus.

## Team

[Juvan Thavalingam](https://github.zhaw.ch/thavajuv) \
[Tim Müller](https://github.zhaw.ch/muellti3) 
