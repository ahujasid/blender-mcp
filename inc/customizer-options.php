<?php
/**
 * WordPress Customizer-Optionen für das Theme.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_customize_register' ) ) :
	/**
	 * Fügt Einstellungen, Sektionen und Controls zum WordPress Customizer hinzu.
	 *
	 * @param WP_Customize_Manager $wp_customize Theme Customizer object.
	 */
	function kneipp_premium_customize_register( $wp_customize ) {

		// ** 1. Theme Optionen Panel (optional, zur Gruppierung) **
		$wp_customize->add_panel( 'kneipp_premium_options_panel', array(
			'title'    => __( 'Kneipp Theme Optionen', 'kneipp-petershagen-premium' ),
			'priority' => 10, // Ganz oben im Customizer
		) );

		// ** 2. Sektion für Footer-Einstellungen **
		$wp_customize->add_section( 'kneipp_premium_footer_section', array(
			'title'    => __( 'Footer Einstellungen', 'kneipp-petershagen-premium' ),
			'panel'    => 'kneipp_premium_options_panel', // Zuordnung zum Panel
			'priority' => 10,
		) );

		// Setting: Copyright Text
		$wp_customize->add_setting( 'kneipp_premium_copyright_text', array(
			'default'           => sprintf( '&copy; %s %s', date_i18n( 'Y' ), get_bloginfo( 'name' ) ),
			'sanitize_callback' => 'wp_kses_post', // Erlaubt grundlegendes HTML
			'transport'         => 'postMessage', // Für Live-Vorschau mit JS (siehe customizer.js)
		) );
		$wp_customize->add_control( 'kneipp_premium_copyright_text_control', array(
			'label'    => __( 'Copyright Text', 'kneipp-petershagen-premium' ),
			'section'  => 'kneipp_premium_footer_section',
			'settings' => 'kneipp_premium_copyright_text',
			'type'     => 'textarea',
		) );

        // Setting: Footer "Stolz präsentiert von" Text anzeigen/ausblenden
        $wp_customize->add_setting( 'kneipp_premium_show_proudly_powered', array(
            'default'           => true,
            'sanitize_callback' => 'kneipp_premium_sanitize_checkbox',
            'transport'         => 'refresh', // Oder postMessage mit JS
        ) );
        $wp_customize->add_control( 'kneipp_premium_show_proudly_powered_control', array(
            'label'    => __( '"Stolz präsentiert von WordPress" anzeigen?', 'kneipp-petershagen-premium' ),
            'section'  => 'kneipp_premium_footer_section',
            'settings' => 'kneipp_premium_show_proudly_powered',
            'type'     => 'checkbox',
        ) );


		// ** 3. Sektion für Kontaktinformationen (Beispiel) **
		$wp_customize->add_section( 'kneipp_premium_contact_section', array(
			'title'    => __( 'Kontaktinformationen', 'kneipp-petershagen-premium' ),
			'panel'    => 'kneipp_premium_options_panel',
			'priority' => 20,
		) );

		// Setting: Telefonnummer
		$wp_customize->add_setting( 'kneipp_premium_phone_number', array(
			'default'           => '',
			'sanitize_callback' => 'sanitize_text_field',
			'transport'         => 'postMessage',
		) );
		$wp_customize->add_control( 'kneipp_premium_phone_number_control', array(
			'label'    => __( 'Telefonnummer', 'kneipp-petershagen-premium' ),
			'section'  => 'kneipp_premium_contact_section',
			'settings' => 'kneipp_premium_phone_number',
			'type'     => 'tel',
		) );

		// Setting: E-Mail-Adresse
		$wp_customize->add_setting( 'kneipp_premium_email_address', array(
			'default'           => '',
			'sanitize_callback' => 'sanitize_email',
			'transport'         => 'postMessage',
		) );
		$wp_customize->add_control( 'kneipp_premium_email_address_control', array(
			'label'    => __( 'E-Mail-Adresse', 'kneipp-petershagen-premium' ),
			'section'  => 'kneipp_premium_contact_section',
			'settings' => 'kneipp_premium_email_address',
			'type'     => 'email',
		) );

		// ** 4. Sektion für Header-Bilder **
		$wp_customize->add_section( 'kneipp_premium_header_image_section', array(
			'title'    => __( 'Header Bilder', 'kneipp-petershagen-premium' ),
			'panel'    => 'kneipp_premium_options_panel',
			'priority' => 5,
		) );

		// Setting: Standard Header-Bild
		$wp_customize->add_setting( 'default_header_bild', array(
			'default'           => KNEIPP_PREMIUM_THEME_URI . 'assets/images/default-header.webp', // Pfad zum Default-Bild im Theme
			'sanitize_callback' => 'esc_url_raw',
			'transport'         => 'refresh', // oder postMessage, wenn JS-Handler vorhanden
		) );
		$wp_customize->add_control( new WP_Customize_Image_Control( $wp_customize, 'default_header_bild_control', array(
			'label'    => __( 'Standard Header-Bild', 'kneipp-petershagen-premium' ),
			'description' => __( 'Dieses Bild wird verwendet, wenn kein spezifisches Header-Bild für eine Seite oder die Startseite gesetzt ist.', 'kneipp-petershagen-premium' ),
			'section'  => 'kneipp_premium_header_image_section',
			'settings' => 'default_header_bild',
		) ) );

		// Setting: Startseiten Header-Bild
		$wp_customize->add_setting( 'startseiten_header_bild', array(
			'default'           => '', // Standardmäßig leer, damit das Default-Header-Bild greift oder ein seiten-spezifisches
			'sanitize_callback' => 'esc_url_raw',
			'transport'         => 'refresh',
		) );
		$wp_customize->add_control( new WP_Customize_Image_Control( $wp_customize, 'startseiten_header_bild_control', array(
			'label'    => __( 'Header-Bild für die Startseite', 'kneipp-petershagen-premium' ),
			'description' => __( 'Laden Sie hier ein spezifisches Bild für den Header der Startseite hoch. Wenn leer, wird das Standard Header-Bild verwendet.', 'kneipp-petershagen-premium' ),
			'section'  => 'kneipp_premium_header_image_section',
			'settings' => 'startseiten_header_bild',
		) ) );


        // Weitere Sektionen und Einstellungen können hier hinzugefügt werden, z.B. für:
        // - Social Media Links
        // - Blog-Layout-Optionen
        // - Farbschemata (obwohl theme.json hierfür oft besser ist)

		// Hinweis: Für 'transport' => 'postMessage' wird eine JavaScript-Datei benötigt,
		// die auf Änderungen im Customizer lauscht und die Vorschau live aktualisiert.
		// Diese Datei muss via 'customize_preview_init' Hook eingebunden werden.
	}
endif;
add_action( 'customize_register', 'kneipp_premium_customize_register' );


if ( ! function_exists( 'kneipp_premium_customize_preview_js' ) ) :
	/**
	 * Bindet JavaScript für die Live-Vorschau im Customizer ein.
	 * Wird nur benötigt, wenn Einstellungen mit 'transport' => 'postMessage' verwendet werden.
	 */
	function kneipp_premium_customize_preview_js() {
        // Annahme: customizer.js liegt in assets/js/
        $js_file_path = KNEIPP_PREMIUM_THEME_DIR . 'assets/js/customizer.js';
        if ( file_exists( $js_file_path ) ) {
		    wp_enqueue_script(
                'kneipp-premium-customizer-preview',
                KNEIPP_PREMIUM_THEME_URI . 'assets/js/customizer.js',
                array( 'customize-preview', 'jquery' ), // Abhängigkeit von jQuery für einfaches DOM-Handling
                filemtime( $js_file_path ),
                true // Im Footer laden
            );
        }
	}
endif;
add_action( 'customize_preview_init', 'kneipp_premium_customize_preview_js' );


if ( ! function_exists( 'kneipp_premium_sanitize_checkbox' ) ) :
    /**
     * Sanitize Callback für Checkbox-Einstellungen im Customizer.
     *
     * @param bool $checked Ob die Checkbox angehakt ist oder nicht.
     * @return bool True wenn angehakt, false sonst.
     */
    function kneipp_premium_sanitize_checkbox( $checked ) {
        // Gibt true zurück, wenn $checked true ist, andernfalls false.
        return ( ( isset( $checked ) && true === $checked ) ? true : false );
    }
endif;

// Weitere sanitize_callback Funktionen für spezifische Feldtypen können hier definiert werden.
// Beispiele:
// - sanitize_select (um sicherzustellen, dass der Wert einer der erlaubten Optionen entspricht)
// - sanitize_hex_color (für Farbeinstellungen)
// - wp_kses_post (für Textareas, die HTML erlauben sollen)
// - absint (für positive Ganzzahlen)

/**
 * Beispiel für die Ausgabe einer Customizer-Einstellung im Theme:
 *
 * Im Footer (z.B. footer.php):
 * <?php
 * $copyright_text = get_theme_mod( 'kneipp_premium_copyright_text', sprintf( '&copy; %s %s', date_i18n( 'Y' ), get_bloginfo( 'name' ) ) );
 * echo wp_kses_post( $copyright_text );
 * ?>
 *
 * Für 'transport' => 'postMessage' muss das entsprechende Element im DOM eine ID oder eindeutige Klasse haben,
 * damit customizer.js es per JavaScript aktualisieren kann.
 * Beispiel: <span class="site-copyright"><?php echo wp_kses_post( $copyright_text ); ?></span>
 *
 * In customizer.js:
 * wp.customize( 'kneipp_premium_copyright_text', function( value ) {
 *     value.bind( function( newval ) {
 *         $( '.site-copyright' ).html( newval );
 *     } );
 * } );
 */
?>
