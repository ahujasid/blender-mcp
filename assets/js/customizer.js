/**
 * JavaScript für die Live-Vorschau im WordPress Customizer.
 *
 * Diese Datei wird via customize_preview_init Hook geladen.
 * Sie behandelt Einstellungen mit 'transport' => 'postMessage'.
 *
 * @package Kneippverein_Petershagen_Premium
 */

( function( $ ) {

    // Beispiel: Live-Aktualisierung für den Copyright-Text
    wp.customize( 'kneipp_premium_copyright_text', function( value ) {
        value.bind( function( newval ) {
            // Annahme: Das Element für den Copyright-Text hat die Klasse '.site-copyright'
            // oder eine spezifischere ID, die im Footer (footer.php) gesetzt wird.
            // Für dieses Beispiel nehmen wir an, es ist Teil von .site-info p
            var $copyrightElement = $( '.site-info p' ).first(); // Vereinfachte Annahme
            if ( $copyrightElement.length ) {
                // Nur den Copyright-Teil aktualisieren, nicht den ganzen Absatz, falls möglich.
                // Dies erfordert ggf. ein separates Span-Element um den Copyright-Text.
                // Hier eine einfache Ersetzung des ersten p-Tags im .site-info:
                // $copyrightElement.html( newval + ' | Stolz präsentiert von WordPress. | Theme: Kneippverein Petershagen Premium von [Ihr Name/Agenturname]' );
                // Besser: Ein dediziertes Element für den Copyright-Text im Footer verwenden und dessen Inhalt aktualisieren.
                // z.B. <span id="footer-copyright-text"></span>
                $('#footer-copyright-text').html(newval); // Wenn ein <span id="footer-copyright-text"> existiert
            }
        } );
    } );

    // Beispiel: Live-Aktualisierung für die Telefonnummer
    wp.customize( 'kneipp_premium_phone_number', function( value ) {
        value.bind( function( newval ) {
            // Annahme: Es gibt ein Element mit der Klasse .contact-phone, das die Telefonnummer anzeigt
            var $phoneElement = $( '.contact-phone a' ); // Falls es ein Link ist
            if ( $phoneElement.length ) {
                $phoneElement.attr( 'href', 'tel:' + newval.replace(/\s/g, '') ); // Leerzeichen für tel: entfernen
                $phoneElement.text( newval );
            } else {
                // Fallback, falls es nur Text ist
                $( '.contact-phone' ).text( newval );
            }
        } );
    } );

    // Beispiel: Live-Aktualisierung für die E-Mail-Adresse
    wp.customize( 'kneipp_premium_email_address', function( value ) {
        value.bind( function( newval ) {
            // Annahme: Es gibt ein Element mit der Klasse .contact-email, das die E-Mail anzeigt
            var $emailElement = $( '.contact-email a' ); // Falls es ein Link ist
             if ( $emailElement.length ) {
                $emailElement.attr( 'href', 'mailto:' + newval );
                $emailElement.text( newval );
            } else {
                $( '.contact-email' ).text( newval );
            }
        } );
    } );

    // Weitere 'postMessage' Einstellungen können hier hinzugefügt werden.
    // z.B. für Schriftfarben, Hintergrundfarben etc., was aber oft besser
    // direkt über die von WordPress generierten CSS-Variablen aus theme.json geschieht.

    /*
    // Beispiel für Farbänderung (wenn nicht über theme.json gesteuert)
    wp.customize( 'meine_hintergrundfarbe_setting', function( value ) {
        value.bind( function( newval ) {
            $( 'body' ).css( 'background-color', newval );
        } );
    } );
    */

} )( jQuery );
