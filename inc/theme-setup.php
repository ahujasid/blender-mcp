<?php
/**
 * Theme Setup Funktionen
 *
 * Hier werden grundlegende Theme-Einstellungen, Supports und Menü-Registrierungen vorgenommen.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_setup' ) ) :
	/**
	 * Richtet Theme-Standardeinstellungen ein und registriert Unterstützung für verschiedene WordPress-Funktionen.
	 *
	 * Beachten Sie, dass diese Funktion an den Hook 'after_setup_theme' gehängt wird,
	 * der vor dem 'init' Hook ausgeführt wird. Einige Hooks sind hier möglicherweise noch nicht verfügbar.
	 */
	function kneipp_premium_setup() {
		/*
		 * Theme für Übersetzungen vorbereiten.
		 * Übersetzungen können im /languages/ Verzeichnis abgelegt werden.
		 * Wenn Sie ein Child-Theme erstellen, das diese Funktion verwendet, verwenden Sie
		 * eine find-and-replace, um KNEIPP_PREMIUM_TEXT_DOMAIN durch den Textdomain
		 * Ihres Child-Themes zu ersetzen.
		 */
		load_theme_textdomain( KNEIPP_PREMIUM_TEXT_DOMAIN, KNEIPP_PREMIUM_THEME_DIR . '/languages' );

		// Automatische Feed-Links für Beiträge und Kommentare im Head hinzufügen.
		add_theme_support( 'automatic-feed-links' );

		/*
		 * WordPress die Verwaltung des Dokumententitels überlassen.
		 * Durch Hinzufügen von Theme-Support erklären wir, dass wir kein hartcodiertes
		 * <title> Tag im Dokumenten-Head verwenden und erwarten, dass WordPress
		 * es für uns bereitstellt.
		 */
		add_theme_support( 'title-tag' );

		/*
		 * Unterstützung für Beitragsbilder (Featured Images) aktivieren.
		 * Siehe https://developer.wordpress.org/themes/functionality/featured-images-post-thumbnails/
		 */
		add_theme_support( 'post-thumbnails' );
        // Standardgröße für Beitragsbilder (kann angepasst werden)
        set_post_thumbnail_size( 800, 600, true ); // Breite, Höhe, Crop (true/false)
        // Weitere Bildgrößen können hier definiert werden, z.B. für Teaser, Galerien etc.
        // add_image_size( 'kneipp-premium-teaser', 400, 300, true );
        // add_image_size( 'kneipp-premium-fullwidth', 1200, 700, true );

		// Dieses Theme verwendet wp_nav_menu() an einer oder mehreren Stellen.
		register_nav_menus(
			array(
				'primary' => esc_html__( 'Primäres Menü (5 Säulen)', 'kneipp-petershagen-premium' ),
				'footer'  => esc_html__( 'Footer Menü', 'kneipp-petershagen-premium' ),
				'social'  => esc_html__( 'Social Media Links', 'kneipp-petershagen-premium' ),
			)
		);

		/*
		 * Zu HTML5-konformem Markup für Suchformulare, Kommentarformulare und Kommentare wechseln.
		 */
		add_theme_support(
			'html5',
			array(
				'search-form',
				'comment-form',
				'comment-list',
				'gallery',
				'caption',
				'style',
				'script',
			)
		);

		// Unterstützung für selektives Aktualisieren von Widgets im Customizer.
		add_theme_support( 'customize-selective-refresh-widgets' );

		// Unterstützung für Core Block Patterns (ab WP 5.5).
		add_theme_support( 'wp-block-styles' );

		// Unterstützung für Full Site Editing Block Themes (ab WP 5.8).
        // add_theme_support( 'block-templates' ); // Nur wenn es ein reines Block Theme sein soll

		// Editor-Stile aktivieren, damit der Gutenberg-Editor dem Frontend ähnelt.
		add_theme_support( 'editor-styles' );
		// Die Datei editor-styles.css wird in enqueue-assets.php eingebunden.
		// Stellen Sie sicher, dass die Datei assets/css/editor-styles.css existiert.
		add_editor_style( 'assets/css/editor-styles.css' );


		// Unterstützung für responsives Einbetten (ab WP 5.5).
		add_theme_support( 'responsive-embeds' );

        // Standard-Breite für Inhalte im Theme setzen (beeinflusst z.B. "alignwide" und "alignfull" Blöcke)
        // Dieser Wert sollte mit den `contentSize` und `wideSize` Werten in `theme.json` korrespondieren.
        if ( ! isset( $content_width ) ) {
            $content_width = 800; // Entspricht contentSize in theme.json
        }

        // Custom Logo Unterstützung
        add_theme_support( 'custom-logo', array(
            'height'      => 100, // Maximale Höhe
            'width'       => 300, // Maximale Breite
            'flex-height' => true,
            'flex-width'  => true,
            // 'header-text' => array( 'site-title', 'site-description' ), // Um Seitentitel/Beschreibung auszublenden, wenn Logo da ist
        ) );

        // Custom Background Unterstützung (optional)
        // add_theme_support( 'custom-background', apply_filters( 'kneipp_premium_custom_background_args', array(
        //  'default-color' => 'ffffff',
        //  'default-image' => '',
        // ) ) );

        // Starter Content (optional, für neue Installationen)
        // add_theme_support( 'starter-content', array( /* ... */ ) );

	}
endif;
add_action( 'after_setup_theme', 'kneipp_premium_setup' );


if ( ! function_exists( 'kneipp_premium_primary_menu_fallback' ) ) :
    /**
     * Fallback-Funktion für das primäre Menü, falls kein Menü zugewiesen ist.
     * Zeigt einen Hinweis an Administratoren, ein Menü zu erstellen.
     */
    function kneipp_premium_primary_menu_fallback() {
        if ( current_user_can( 'manage_options' ) ) {
            echo '<ul id="primary-menu" class="menu-primary">';
            echo '<li><a href="' . esc_url( admin_url( 'nav-menus.php' ) ) . '">' . esc_html__( 'Primäres Menü zuweisen (5 Säulen)', 'kneipp-petershagen-premium' ) . '</a></li>';
            echo '</ul>';
        }
    }
endif;

if ( ! function_exists( 'kneipp_premium_content_width' ) ) :
    /**
     * Setzt die Inhaltsbreite basierend auf dem Theme-Design und den Stylesheets.
     * Wird von WordPress für oEmbeds und andere Inhaltsbreiten-abhängige Funktionen verwendet.
     */
    function kneipp_premium_content_width() {
        // Dieser Wert sollte mit `settings.layout.contentSize` in `theme.json` übereinstimmen.
        // $GLOBALS['content_width'] wird von WordPress an verschiedenen Stellen verwendet.
        $GLOBALS['content_width'] = apply_filters( 'kneipp_premium_content_width', 800 );
    }
endif;
add_action( 'after_setup_theme', 'kneipp_premium_content_width', 0 );


if ( ! function_exists( 'kneipp_premium_widgets_init' ) ) :
    /**
     * Registriert Widget-Bereiche (Sidebars).
     *
     * @link https://developer.wordpress.org/themes/functionality/sidebars/#registering-a-sidebar
     */
    function kneipp_premium_widgets_init() {
        register_sidebar(
            array(
                'name'          => esc_html__( 'Primäre Sidebar', 'kneipp-petershagen-premium' ),
                'id'            => 'sidebar-1',
                'description'   => esc_html__( 'Fügen Sie hier Widgets hinzu, die in Ihrer Sidebar angezeigt werden sollen.', 'kneipp-petershagen-premium' ),
                'before_widget' => '<section id="%1$s" class="widget %2$s">',
                'after_widget'  => '</section>',
                'before_title'  => '<h2 class="widget-title">',
                'after_title'   => '</h2>',
            )
        );
        register_sidebar(
            array(
                'name'          => esc_html__( 'Footer Widget Bereich 1', 'kneipp-petershagen-premium' ),
                'id'            => 'footer-1',
                'description'   => esc_html__( 'Widgets für die erste Spalte im Footer.', 'kneipp-petershagen-premium' ),
                'before_widget' => '<section id="%1$s" class="widget footer-widget %2$s">',
                'after_widget'  => '</section>',
                'before_title'  => '<h3 class="widget-title">',
                'after_title'   => '</h3>',
            )
        );
        // Weitere Footer Widget Bereiche können hier registriert werden (footer-2, footer-3 etc.)
    }
endif;
add_action( 'widgets_init', 'kneipp_premium_widgets_init' );

/**
 * Fügt benutzerdefinierte Klassen zum Body-Tag hinzu.
 *
 * @param array $classes Klassen für das body-Element.
 * @return array
 */
function kneipp_premium_body_classes( $classes ) {
	// Fügt eine Klasse von 'no-sidebar' hinzu, wenn keine Sidebar aktiv ist.
	if ( ! is_active_sidebar( 'sidebar-1' ) ) {
		$classes[] = 'no-sidebar';
	}

    // Fügt eine Klasse hinzu, wenn wir uns auf einer Einzelseite oder einem Einzelbeitrag befinden.
	if ( is_singular() && ! is_front_page() ) {
		$classes[] = 'singular';
	}

    // Fügt eine Klasse für die mobile Navigation hinzu (kann per JS getoggelt werden)
    // $classes[] = 'mobile-nav-inactive';

	return $classes;
}
add_filter( 'body_class', 'kneipp_premium_body_classes' );

/**
 * Pingback Header für Singular-Ansichten.
 */
function kneipp_premium_pingback_header() {
	if ( is_singular() && pings_open() ) {
		printf( '<link rel="pingback" href="%s">', esc_url( get_bloginfo( 'pingback_url' ) ) );
	}
}
add_action( 'wp_head', 'kneipp_premium_pingback_header' );

// Weitere Setup-Funktionen, wie z.B. das Entfernen von WordPress-Versionsnummern, Emojis etc.
// können in separaten Dateien im /inc/ Ordner (z.B. security.php oder performance.php) platziert
// und von der functions.php geladen werden.
?>
