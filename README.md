# Kneippverein Petershagen Premium WordPress Theme

Version: 1.0.0
Entwickelt für: Kneippverein Petershagen e.V.
Konzept von: Jules KI
Umsetzung durch: [Ihr Name/Agenturname hier einfügen]

## Beschreibung

Ein maßgeschneidertes Premium-WordPress-Theme für den Kneippverein Petershagen e.V., entwickelt für höchste Ansprüche an Design, Funktionalität, Barrierefreiheit und Performance. Dieses Theme bietet eine solide Grundlage für eine moderne und zukunftssichere Online-Präsenz, die die Kneipp-Lehre optimal vermittelt.

Es ist mit Fokus auf den Gutenberg-Editor konzipiert, um eine maximale Flexibilität und eine intuitive Bedienung für Redakteure zu gewährleisten.

## Hauptmerkmale (geplant)

*   **Responsives Design (Mobile First):** Optimale Darstellung auf allen Endgeräten.
*   **WCAG-konform (AA-Niveau als Ziel):** Hohe Zugänglichkeit für alle Nutzer.
*   **Performance-Optimierung:** Schnelle Ladezeiten durch Critical CSS, Lazy Loading, optimierte Bilder und saubere Requests.
*   **Gutenberg-zentriert:** Umfassende Unterstützung des Gutenberg-Editors, inklusive `theme.json` für globale Stile und individuelle Block-Styles.
*   **Custom Post Types:** Für "Kurse", "Veranstaltungen", "Rezepte" und "Teammitglieder" (oder ähnlich).
*   **Individuelle Gutenberg-Blöcke / ACF-Blöcke:** Für modulare und wiederverwendbare Inhaltskomponenten.
*   **SEO-Basics integriert:** Saubere semantische Struktur, Breadcrumbs, Vorbereitung für strukturierte Daten.
*   **Modulare Codebasis:** Gut strukturierte `functions.php` durch Aufteilung in `inc/` Verzeichnis.
*   **Child-Theme-Ready:** Struktur ermöglicht einfache Anpassungen über ein Child-Theme.
*   **Mehrsprachigkeit vorbereitet:** Inklusive Textdomain und `.pot`-Datei.
*   **Umfassende Fehlerbehandlung:** Gestaltete `404.php`, `search.php` etc.

## Verzeichnisstruktur

```
/kneipp-petershagen-premium/
|-- /assets/                 # CSS, JS, Bilder, Fonts, Icons
|-- /inc/                    # PHP Include-Dateien (Modularisierung der functions.php)
|-- /languages/              # Sprachdateien (.pot, .po, .mo)
|-- /parts/                  # Wiederverwendbare Template-Teile
|-- /templates/              # Seiten-Templates und spezifische Templates für CPTs etc.
|-- /docs/                   # Dokumentation
|-- style.css                # Haupt-Stylesheet (Theme-Header)
|-- functions.php            # Haupt-Funktionsdatei
|-- theme.json               # Globale Stile und Einstellungen für Gutenberg
|-- index.php                # Standard-Fallback-Template
|-- header.php               # Standard-Header
|-- footer.php               # Standard-Footer
|-- page.php                 # Standard-Template für Seiten
|-- single.php               # Standard-Template für einzelne Beiträge
|-- archive.php              # Standard-Template für Archivseiten
|-- search.php               # Template für Suchergebnisse
|-- 404.php                  # Template für "Seite nicht gefunden" Fehler
|-- screenshot.png           # Theme-Vorschaubild
|-- README.md                # Diese Datei
|-- .editorconfig            # Editor-Konfiguration (optional)
|-- .gitignore               # Ignorierte Dateien für Git (optional)
|-- package.json             # Für npm-Abhängigkeiten (Build-Tools, optional)
|-- vite.config.js           # Beispiel für Vite Konfiguration (oder webpack.config.js, optional)
```

## Installation

1.  Laden Sie das Theme-Verzeichnis `kneipp-petershagen-premium` in das `/wp-content/themes/` Verzeichnis Ihrer WordPress-Installation hoch.
2.  Alternativ können Sie das Theme als ZIP-Datei packen und über das WordPress-Admin-Panel unter "Design" > "Themes" > "Theme hinzufügen" > "Theme hochladen" installieren.
3.  Aktivieren Sie das Theme im WordPress-Admin-Panel unter "Design" > "Themes".

## Entwicklung (Optional, bei Verwendung eines Build-Prozesses)

Dieses Theme ist für die moderne Frontend-Entwicklung mit einem Build-Prozess (z.B. Vite oder Webpack) für SCSS und JavaScript vorgesehen.

1.  Stellen Sie sicher, dass Node.js und npm (oder yarn) installiert sind.
2.  Navigieren Sie im Terminal in das Theme-Verzeichnis: `cd wp-content/themes/kneipp-petershagen-premium`
3.  Installieren Sie die Projektabhängigkeiten: `npm install` (oder `yarn install`)
4.  Starten Sie den Entwicklungs-Server: `npm run dev` (oder `yarn dev`)
5.  Für einen Produktions-Build: `npm run build` (oder `yarn build`)

Die entsprechenden Skripte müssen in der `package.json` definiert sein. Die Dateien `assets/css/main.css` und `assets/js/main.js` werden durch diesen Prozess erstellt.

## Anpassung

*   **Child-Theme:** Für umfangreichere Anpassungen wird dringend empfohlen, ein Child-Theme zu erstellen, um die Update-Fähigkeit des Premium-Themes zu erhalten.
*   **WordPress Customizer:** Viele grundlegende Einstellungen (Logo, Farben, Menüs, Widgets) können über den WordPress Customizer (Design > Customizer) vorgenommen werden.
*   **Theme Options:** Erweiterte Optionen können über ein integriertes Theme-Options-Framework (z.B. ACF Pro, Kirki) oder den Customizer bereitgestellt werden.
*   **`theme.json`:** Globale Stile, Block-Stile und Layout-Einstellungen werden zentral in der `theme.json` verwaltet.
*   **Action Hooks und Filter:** Das Theme wird diverse Hooks und Filter bereitstellen, um eine einfache Erweiterung der Funktionalität zu ermöglichen (siehe Entwicklerdokumentation).

## Menüstruktur (Vorschlag basierend auf 5 Säulen)

Im WordPress-Backend unter "Design" > "Menüs" sollte ein Hauptmenü mit dem Namen "Primäres Menü (5 Säulen)" (oder ähnlich) erstellt werden. Dieses Menü kann dann wie folgt strukturiert werden:

1.  **Startseite**
2.  **Die 5 Säulen** (ggf. als Oberpunkt ohne Link oder mit einer Übersichtsseite)
    *   Wasser (Link zur Seite/Kategorie "Wasser")
    *   Pflanzen (Link zur Seite/Kategorie "Pflanzen")
    *   Bewegung (Link zur Seite/Kategorie "Bewegung")
    *   Ernährung (Link zur Seite/Kategorie "Ernährung")
    *   Balance (Link zur Seite/Kategorie "Balance")
3.  **Kurse & Angebote** (Link zur Kursübersichtsseite - Archive-CPT)
4.  **Veranstaltungen** (Link zur Veranstaltungsübersichtsseite - Archive-CPT)
5.  **Über uns**
    *   Unser Verein
    *   Team
    *   Mitglied werden
    *   Geschichte Sebastian Kneipps (Link zur Seite "Geschichte Sebastian Kneipps")
6.  **Kontakt**

Dieses Menü wird dann der Theme-Position "Primäres Menü (5 Säulen)" zugewiesen, die in `inc/theme-setup.php` registriert wurde.

## Lizenz

Dieses Theme ist unter der GNU General Public License v2 oder später lizenziert.
Siehe den Header der `style.css`.

## Support und Dokumentation

Eine detaillierte Dokumentation ist entscheidend für die Wartung und Nutzung des Themes.

*   **Entwicklerdokumentation:** Findet sich in `docs/entwickler-doku.md`. Diese Datei enthält technische Details zur Theme-Architektur, Hooks, Filter, Anleitung zur Blockentwicklung und Child-Theme-Erstellung.
*   **Redakteursanleitung:** Findet sich in `docs/redakteur-anleitung.md`. Diese Datei bietet eine Anleitung für Redakteure zur optimalen Nutzung der Theme-Features, Custom Post Types, individuellen Blöcke und Theme-Optionen.
*   **Inline-Code-Kommentare:** Der PHP-, JS- und CSS-Code ist durchgehend kommentiert, um die Lesbarkeit und Verständlichkeit zu erhöhen. PHPDoc-Blöcke werden für Funktionen und Klassen verwendet.
*   **Changelog:** Änderungen und Versionen werden idealerweise in einem `CHANGELOG.md` (nicht erstellt) oder über Git-Tags dokumentiert.

---

Dieses `README.md` dient als erste Orientierung und wird im Laufe der Entwicklung weiter detailliert. Die Dateien `assets/css/editor-styles.css`, `assets/css/main.css` und `assets/js/main.js` müssen noch erstellt werden (main.css und main.js typischerweise durch einen Build-Prozess).
