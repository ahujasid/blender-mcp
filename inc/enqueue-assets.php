<?php
/**
 * Einbinden von Stylesheets und JavaScript-Dateien
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_scripts_styles' ) ) :
	/**
	 * Lädt Theme-Stylesheets und Skripte.
	 */
	function kneipp_premium_scripts_styles() {
		// Theme Stylesheet (style.css - primär für Theme Header, Hauptstile kommen aus main.css)
		wp_enqueue_style(
			'kneipp-premium-style',
			get_stylesheet_uri(),
			array(),
			KNEIPP_PREMIUM_THEME_VERSION
		);

		// Haupt-Stylesheet (kompiliert aus SCSS/PostCSS, z.B. assets/css/main.css)
		// Diese Datei sollte alle Frontend-Stile des Themes enthalten.
		// Die Erstellung (Build-Prozess) dieser Datei ist nicht Teil dieses PHP-Skripts.
		if ( file_exists( KNEIPP_PREMIUM_THEME_DIR . 'assets/css/main.css' ) ) {
			wp_enqueue_style(
				'kneipp-premium-main-styles',
				KNEIPP_PREMIUM_THEME_URI . 'assets/css/main.css',
				array('kneipp-premium-style'), // Abhängigkeit von style.css (optional)
				filemtime( KNEIPP_PREMIUM_THEME_DIR . 'assets/css/main.css' ) // Cache Busting basierend auf Dateiänderungsdatum
			);
		} else {
            // Fallback oder Hinweis, falls main.css fehlt
            wp_add_inline_style('kneipp-premium-style', '/* Haupt-CSS (main.css) nicht gefunden. Bitte Build-Prozess ausführen. */');
        }

		// Google Fonts (Beispiel: Open Sans und Montserrat aus theme.json).
        // WordPress bindet diese automatisch ein, wenn sie in theme.json via fontFace definiert sind und die Dateien existieren.
        // Alternativ oder zusätzlich kann man sie hier manuell enqueuen:
		/*
        wp_enqueue_style(
            'kneipp-premium-google-fonts',
            'https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&family=Montserrat:wght@400;700;900&display=swap',
            array(),
            null // Keine Version für externe Ressourcen
        );
        */


		// Haupt-JavaScript-Datei (kompiliert, z.B. assets/js/main.js)
        // Diese Datei sollte alle Frontend-Skripte des Themes enthalten.
		if ( file_exists( KNEIPP_PREMIUM_THEME_DIR . 'assets/js/main.js' ) ) {
			wp_enqueue_script(
				'kneipp-premium-main-scripts',
				KNEIPP_PREMIUM_THEME_URI . 'assets/js/main.js',
				array( 'jquery' ), // Abhängigkeiten, z.B. jQuery (WordPress liefert jQuery mit)
				filemtime( KNEIPP_PREMIUM_THEME_DIR . 'assets/js/main.js' ), // Cache Busting
				true // Im Footer laden
			);
            // Lokalisierung von Skripten (Daten von PHP an JS übergeben)
            // wp_localize_script('kneipp-premium-main-scripts', 'kneippPremiumGlobal', array(
            // 'ajaxUrl' => admin_url('admin-ajax.php'),
            // 'nonce'   => wp_create_nonce('kneipp_premium_nonce'),
            // 'isMobile' => wp_is_mobile(),
            // 'labels' => array(
            //      'loading' => __('Lädt...', KNEIPP_PREMIUM_TEXT_DOMAIN)
            // )
            // ));
		} else {
            // Fallback oder Hinweis, falls main.js fehlt
            // (Kann über wp_add_inline_script gemacht werden, wenn jQuery geladen ist)
        }


		// Kommentar-Antwort-Skript (nur auf Einzelseiten/Beiträgen mit aktivierten Kommentaren)
		if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
			wp_enqueue_script( 'comment-reply' );
		}

        // Optional: Skripte für individuelle Gutenberg Blöcke
        // if ( file_exists( KNEIPP_PREMIUM_THEME_DIR . 'assets/js/custom-blocks.js' ) && is_singular() ) {
        //    wp_enqueue_script(
        //        'kneipp-premium-custom-blocks',
        //        KNEIPP_PREMIUM_THEME_URI . 'assets/js/custom-blocks.js',
        //        array('wp-blocks', 'wp-element', 'wp-i18n', 'wp-editor'), // Abhängigkeiten für Block-JS
        //        filemtime( KNEIPP_PREMIUM_THEME_DIR . 'assets/js/custom-blocks.js' ),
        //        true
        //    );
        // }

	}
endif;
add_action( 'wp_enqueue_scripts', 'kneipp_premium_scripts_styles' );


if ( ! function_exists( 'kneipp_premium_editor_styles' ) ) :
    /**
     * Lädt zusätzliche Stylesheets für den Gutenberg-Editor.
     * Die Haupt-Editor-Styles werden via add_editor_style() in theme-setup.php deklariert.
     * Hier können z.B. Google Fonts spezifisch für den Editor geladen werden, falls nötig.
     */
    function kneipp_premium_editor_styles() {
        // Stellt sicher, dass assets/css/editor-styles.css existiert und via add_editor_style() geladen wird.
        // Diese Funktion kann für zusätzliche Editor-Assets wie Google Fonts genutzt werden,
        // falls sie nicht schon global geladen werden oder in theme.json definiert sind.
        /*
        wp_enqueue_style(
            'kneipp-premium-editor-google-fonts',
            'https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&family=Montserrat:wght@400;700;900&display=swap',
            array(),
            null
        );
        */
        // Wichtig: Die `editor-styles.css` sollte die Frontend-Styles möglichst genau widerspiegeln.
        // Sie kann Stile aus `main.css` importieren oder relevante Teile davon duplizieren/anpassen.
    }
endif;
add_action( 'enqueue_block_editor_assets', 'kneipp_premium_editor_styles' );


if ( ! function_exists( 'kneipp_premium_admin_styles' ) ) :
    /**
     * Lädt zusätzliche Stylesheets für den WordPress Admin-Bereich (optional).
     */
    function kneipp_premium_admin_styles() {
        if ( file_exists( KNEIPP_PREMIUM_THEME_DIR . 'assets/css/admin-styles.css' ) ) {
            wp_enqueue_style(
                'kneipp-premium-admin-styles',
                KNEIPP_PREMIUM_THEME_URI . 'assets/css/admin-styles.css',
                array(),
                filemtime( KNEIPP_PREMIUM_THEME_DIR . 'assets/css/admin-styles.css' )
            );
        }
    }
endif;
// add_action( 'admin_enqueue_scripts', 'kneipp_premium_admin_styles' );


if ( ! function_exists( 'kneipp_premium_login_styles' ) ) :
    /**
     * Lädt zusätzliche Stylesheets für die WordPress Login-Seite (optional).
     */
    function kneipp_premium_login_styles() {
        if ( file_exists( KNEIPP_PREMIUM_THEME_DIR . 'assets/css/login-styles.css' ) ) {
            wp_enqueue_style(
                'kneipp-premium-login-styles',
                KNEIPP_PREMIUM_THEME_URI . 'assets/css/login-styles.css',
                array(),
                filemtime( KNEIPP_PREMIUM_THEME_DIR . 'assets/css/login-styles.css' )
            );
        }
    }
endif;
// add_action( 'login_enqueue_scripts', 'kneipp_premium_login_styles' );

/**
 * Wichtige Hinweise zum Enqueueing:
 * - Performance: Binden Sie Skripte und Stile nur dort ein, wo sie benötigt werden.
 *   Nutzen Sie Conditional Tags (is_page(), is_single(), etc.).
 * - Abhängigkeiten: Definieren Sie Abhängigkeiten korrekt (z.B. 'jquery').
 * - Versionierung/Cache Busting: Verwenden Sie filemtime() für lokale Dateien, um Browser-Caching
 *   bei Änderungen zu umgehen. Für externe Ressourcen setzen Sie die Version auf null oder eine feste Nummer.
 * - Build-Prozess: Für moderne Entwicklung (SCSS, ES6+ JS, Minifizierung, etc.) ist ein Build-Prozess
 *   (z.B. mit Vite, Webpack, Parcel oder Gulp/Grunt) unerlässlich. Dieser kompiliert die Assets
 *   in die Verzeichnisse assets/css und assets/js.
 */
?>
