<?php
/**
 * Barrierefreiheits-spezifische Funktionen und Verbesserungen.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Barrierefreie Formulare: Checkliste und Hinweise
 *
 * Die Implementierung barrierefreier Formulare ist entscheidend.
 * Dieses Theme zielt darauf ab, die Grundlagen dafür zu schaffen und
 * bei der Verwendung von Formular-Plugins auf deren korrekte Konfiguration
 * und ggf. Anpassung hinzuwirken.
 *
 * 1. Labels:
 *    - Jedes <input>, <textarea>, <select> MUSS ein assoziiertes <label> haben.
 *    - Verknüpfung über for-Attribut des Labels und id des Feldes.
 *    - Placeholder sind KEIN Ersatz für Labels.
 *    - Labels müssen immer sichtbar sein (Ausnahme: Suchfeld mit sichtbarem Button, wo das Label via .screen-reader-text versteckt sein kann, aber programmatisch vorhanden ist).
 *
 * 2. Gruppierung:
 *    - <fieldset> und <legend> für zusammengehörige Gruppen von Radiobuttons oder Checkboxen verwenden.
 *    - Die <legend> beschreibt die Gruppe.
 *
 * 3. ARIA-Attribute:
 *    - aria-required="true": Für Pflichtfelder.
 *    - aria-invalid="true": Dynamisch setzen, wenn ein Feld nach Validierung ungültig ist.
 *    - aria-describedby: Um Felder mit zusätzlichen Hinweisen oder Fehlermeldungen zu verknüpfen.
 *      Die ID des Elements, das die Beschreibung enthält, wird als Wert für aria-describedby verwendet.
 *      Beispiel: <input id="email" aria-describedby="email-error"> <span id="email-error">Ungültige E-Mail.</span>
 *    - aria-live-Regionen (z.B. mit role="alert" oder aria-live="assertive"): Für dynamisch erscheinende
 *      Fehlermeldungen, damit Screenreader diese Änderungen mitbekommen.
 *
 * 4. Tastaturnavigation:
 *    - Alle interaktiven Formularelemente (Felder, Buttons) müssen per Tab-Taste erreichbar sein.
 *    - Die Fokusreihenfolge muss logisch und intuitiv sein.
 *    - Der Tastaturfokus muss IMMER deutlich sichtbar sein (CSS :focus-visible Stile).
 *      In theme.json und main.css sicherstellen.
 *
 * 5. Fehlermeldungen und Validierung:
 *    - Fehler müssen klar, präzise und direkt beim betreffenden Feld angezeigt werden.
 *    - Serverseitige Validierung ist unerlässlich. Clientseitige Validierung (HTML5, JS) verbessert die UX.
 *    - Nach dem Absenden mit Fehlern sollte der Fokus zum ersten fehlerhaften Feld oder einer Fehlerübersicht springen.
 *    - Fehlermeldungen sollten programmatisch mit dem Feld verbunden sein (aria-describedby).
 *
 * 6. Visuelles Design:
 *    - Ausreichende Klick-/Touch-Flächen.
 *    - Gute Farbkontraste (Text auf Hintergrund, Feldrahmen, Fokusindikatoren).
 *    - Klare visuelle Unterscheidung von Pflichtfeldern (z.B. Sternchen * UND aria-required="true").
 *
 * Implementierung im Theme:
 *
 * a) WordPress Standardformulare:
 *    - Suchformular (searchform.php oder get_search_form Filter):
 *      - Sicherstellen, dass <label for="id_des_suchfelds"> vorhanden ist.
 *      - Such-Button sollte klaren Text haben (ggf. visuell versteckt, wenn Icon verwendet wird).
 *      - Beispiel in `searchform.php` (falls erstellt) oder durch Filter anpassen:
 */
        /*
        add_filter( 'get_search_form', 'kneipp_premium_accessible_search_form' );
        function kneipp_premium_accessible_search_form( $form ) {
            $form_id = 'search-form-' . uniqid(); // Eindeutige ID für Label-Verknüpfung
            $search_field_id = 's-' . uniqid();

            $form = '<form role="search" method="get" class="search-form" id="' . $form_id . '" action="' . esc_url( home_url( '/' ) ) . '">
                        <label for="' . $search_field_id . '" class="screen-reader-text">' . _x( 'Suchen nach:', 'label', 'kneipp-petershagen-premium' ) . '</label>
                        <input type="search" id="' . $search_field_id . '" class="search-field" placeholder="' . esc_attr_x( 'Suchen &hellip;', 'placeholder', 'kneipp-petershagen-premium' ) . '" value="' . get_search_query() . '" name="s" />
                        <button type="submit" class="search-submit">';
            // Annahme: kneipp_premium_get_icon() existiert in template-tags.php
            // $form .= kneipp_premium_get_icon('search');
            $form .= '<span class="screen-reader-text">' . _x( 'Suchen', 'submit button', 'kneipp-petershagen-premium' ) . '</span>
                        </button>
                    </form>';
            return $form;
        }
        */
/**
 *    - Kommentarformular (comment_form()):
 *      - Die Standardargumente wurden bereits in `inc/template-tags.php` (kneipp_premium_comment_form_defaults)
 *        weitgehend barrierefrei gestaltet (Labels, Verknüpfungen).
 *      - CSS-Styling für Fokus und Fehlermeldungen ist wichtig.
 *
 * b) Formular-Plugins (z.B. Contact Form 7, WPForms, Gravity Forms):
 *    - Plugin-Auswahl: Bevorzugen Sie Plugins, die von Haus aus Wert auf Barrierefreiheit legen.
 *    - Markup-Anpassung: Viele Plugins erlauben das Anpassen des HTML-Markups ihrer Formulare
 *      oder bieten Hooks, um ARIA-Attribute hinzuzufügen.
 *    - Styling: Das Theme muss das CSS für diese Plugins bereitstellen oder überschreiben,
 *      um CI-Konformität und Barrierefreiheit (Kontraste, Fokus, Fehlerdarstellung) zu gewährleisten.
 *      Beispiel: Wenn CF7 verwendet wird, könnten spezifische Stile für .wpcf7-form Elemente nötig sein.
 *
 * c) Eigene Formulare (z.B. Kursanmeldung ohne Plugin):
 *    - Hier ist volle Kontrolle und Verantwortung beim Theme-Entwickler.
 *    - Alle oben genannten Punkte (Labels, Fieldsets, ARIA, Validierung, etc.) müssen sorgfältig implementiert werden.
 *
 * d) JavaScript für Barrierefreiheit:
 *    - Dynamisches Setzen von ARIA-Attributen (z.B. aria-invalid nach clientseitiger Validierung).
 *    - Management von aria-live Regionen für dynamische Updates.
 *    - Sicherstellen, dass JS-basierte Formularverbesserungen nicht die Tastaturnavigation oder Screenreader-Funktionalität beeinträchtigen.
 */


if ( ! function_exists( 'kneipp_premium_skip_link_focus_fix' ) ) :
    /**
     * Hilfsfunktion, um den Fokus nach dem Klick auf einen "Skip-Link" korrekt zu setzen.
     * Quelle: Twenty Twenty-One Theme
     */
    function kneipp_premium_skip_link_focus_fix() {
        // Das Skript ist klein, also binden wir es direkt ein.
        ?>
        <script type="text/javascript">
        ( function() {
            var isIe = /(trident|msie)/i.test( navigator.userAgent );
            if ( isIe && document.getElementById && window.addEventListener ) {
                window.addEventListener( 'hashchange', function() {
                    var id = location.hash.substring( 1 );
                    if ( ! ( /^[A-z0-9_-]+$/.test( id ) ) ) {
                        return;
                    }
                    var element = document.getElementById( id );
                    if ( element ) {
                        if ( ! ( /^(?:a|select|input|button|textarea)$/i.test( element.tagName ) ) ) {
                            element.tabIndex = -1;
                        }
                        element.focus();
                    }
                }, false );
            }
        }() );
        </script>
        <?php
    }
endif;
add_action( 'wp_print_footer_scripts', 'kneipp_premium_skip_link_focus_fix' );

// Weitere Helferfunktionen für Barrierefreiheit könnten hier platziert werden,
// z.B. Funktionen zum Hinzufügen von ARIA-Attributen zu Menü-Links,
// oder zur Verbesserung der Fokus-Verwaltung bei modalen Dialogen (falls verwendet).
?>
