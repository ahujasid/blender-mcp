<?php
/**
 * Gutenberg Editor spezifische Anpassungen und Support-Funktionen.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_gutenberg_theme_support' ) ) :
	/**
	 * Fügt Gutenberg-spezifische Theme-Unterstützung hinzu.
	 * Viele grundlegende Supports wie `editor-styles`, `wp-block-styles`
	 * sind bereits in `inc/theme-setup.php` deklariert.
	 * Hier können spezifischere Einstellungen erfolgen.
	 */
	function kneipp_premium_gutenberg_theme_support() {

		// Breite und volle Ausrichtung für Blöcke aktivieren
		add_theme_support( 'align-wide' );

		// Responsive eingebettete Inhalte (z.B. Videos)
		add_theme_support( 'responsive-embeds' );

		// Sicherstellen, dass Editor-Styles geladen werden (bereits in theme-setup.php)
		// add_theme_support( 'editor-styles' );
		// add_editor_style( 'assets/css/editor-styles.css' ); // Pfad zur Editor-CSS-Datei

        // Standard-Block-Patterns des Cores deaktivieren, falls eigene bevorzugt werden
        // remove_theme_support( 'core-block-patterns' );

        // Farbpalette für den Editor definieren (wird primär über theme.json gesteuert)
        // add_theme_support( 'editor-color-palette', array(...) );

        // Schriftgrößen für den Editor definieren (wird primär über theme.json gesteuert)
        // add_theme_support( 'editor-font-sizes', array(...) );

        // Unterstützung für benutzerdefinierte Zeilenhöhe
        add_theme_support( 'custom-line-height' );

        // Unterstützung für benutzerdefinierte Einheiten (px, em, rem, etc.)
        add_theme_support( 'custom-units' );
        // add_theme_support( 'custom-units', 'px', 'rem', 'em', 'vw', 'vh', '%' );


        // Deaktiviere die Möglichkeit, eigene Farben im Editor auszuwählen,
        // um das CI zu wahren (nur Farben aus der Palette erlaubt).
        // add_theme_support( 'disable-custom-colors' );

        // Deaktiviere die Möglichkeit, eigene Schriftgrößen im Editor auszuwählen.
        // add_theme_support( 'disable-custom-font-sizes' );

	}
endif;
add_action( 'after_setup_theme', 'kneipp_premium_gutenberg_theme_support' );


if ( ! function_exists( 'kneipp_premium_allowed_block_types' ) ) :
    /**
     * Definiert eine Whitelist der erlaubten Blöcke im Gutenberg Editor.
     * Hilft, die Auswahl für Redakteure übersichtlich zu halten und das Design konsistent.
     *
     * @param bool|array $allowed_blocks Array der erlaubten Block-Namen oder true, um alle zu erlauben.
     * @param WP_Block_Editor_Context $editor_context Der Kontext des Editors.
     * @return bool|array
     */
    function kneipp_premium_allowed_block_types( $allowed_blocks, $editor_context ) {
        // Nur im Post Editor anwenden, nicht z.B. im Widget Editor
        if ( ! empty( $editor_context->post ) ) {
            return array(
                // Core Blöcke (Beispiele, Liste erweitern oder anpassen)
                'core/paragraph',
                'core/heading',
                'core/list',
                'core/list-item',
                'core/image',
                'core/gallery',
                'core/quote',
                'core/pullquote',
                'core/button',
                'core/buttons',
                'core/columns',
                'core/column',
                'core/group',
                'core/separator',
                'core/spacer',
                'core/table',
                'core/html', // Für erfahrene Nutzer
                'core/shortcode',
                'core/embed', // Generischer Embed-Block

                // Spezifische Embeds (Beispiele)
                'core/embed-youtube',
                'core/embed-vimeo',

                // Eigene Blöcke (Beispiel)
                'kneipp-premium/pillars-teaser', // Unser benutzerdefinierter Block
                // Weitere eigene Blöcke hier hinzufügen...

                // Ggf. Blöcke von vertrauenswürdigen Plugins
                // 'acf/mein-acf-block', // Beispiel für einen ACF Block
            );
        }
        return $allowed_blocks; // Für andere Kontexte (Widgets, FSE) alle Blöcke erlauben
    }
endif;
// add_filter( 'allowed_block_types_all', 'kneipp_premium_allowed_block_types', 10, 2 );


if ( ! function_exists( 'kneipp_premium_block_categories' ) ) :
    /**
     * Fügt eine benutzerdefinierte Kategorie für Theme-spezifische Blöcke hinzu.
     *
     * @param array $categories Array von Block-Kategorien.
     * @param WP_Block_Editor_Context $editor_context Der Kontext des Editors.
     * @return array
     */
    function kneipp_premium_block_categories( $categories, $editor_context ) {
        // Nur im Post Editor anwenden
        // if ( ! empty( $editor_context->post ) ) { // Nicht mehr nötig ab WP 5.8, der Hook ist kontextbezogen
            $custom_category = array(
                'slug'  => 'kneipp-premium-blocks',
                'title' => __( 'Kneipp Premium Blöcke', 'kneipp-petershagen-premium' ),
                'icon'  => 'herbal', // Dashicon (oder SVG)
            );

            // Füge die Kategorie am Anfang oder Ende hinzu
            // return array_merge( array( $custom_category ), $categories ); // Am Anfang
            $categories[] = $custom_category; // Am Ende
        // }
        return $categories;
    }
endif;
// WordPress 6.3 hat den Hook `block_categories_all` eingeführt, der `block_categories` ersetzt und $editor_context übergibt.
// Für Abwärtskompatibilität kann man prüfen, ob der neue Hook existiert.
if ( version_compare( get_bloginfo( 'version' ), '6.3', '>=' ) ) {
    add_filter( 'block_categories_all', 'kneipp_premium_block_categories', 10, 2 );
} else {
    add_filter( 'block_categories', 'kneipp_premium_block_categories', 10, 2 ); // $editor_context ist hier $post
}


/**
 * Registrierung benutzerdefinierter Gutenberg-Blöcke.
 * Hier wird nur die PHP-Seite der Registrierung gezeigt.
 * Die JavaScript-Dateien (Build-Prozess) sind für die Funktionalität im Editor notwendig.
 */
function kneipp_premium_register_custom_blocks() {

    // Prüfen, ob die Funktion existiert (WP 5.0+)
    if ( ! function_exists( 'register_block_type' ) ) {
        return;
    }

    // Pfad zu den kompilierten Block-Assets (JS und CSS)
    // Annahme: Build-Prozess legt sie unter /assets/blocks/ ab
    $blocks_asset_path = KNEIPP_PREMIUM_THEME_DIR . 'assets/blocks/';
    $blocks_asset_url  = KNEIPP_PREMIUM_THEME_URI . 'assets/blocks/';

    // **Beispiel: Kneipp-Säulen Teaser Block**
    // Die eigentlichen JS-Dateien (index.js, edit.js, save.js) müssten unter
    // einem Pfad wie z.B. `src/blocks/pillars-teaser/` liegen und kompiliert werden.
    // Das `block.json` für diesen Block würde dann die Asset-Pfade definieren.

    // Registrierung via `block.json` (bevorzugter Weg ab WP 5.8)
    // WordPress sucht automatisch nach `block.json` Dateien im Theme.
    // Wenn dein Block `kneipp-premium/pillars-teaser` eine `block.json` in
    // `wp-content/themes/dein-theme/build/blocks/pillars-teaser/block.json` hat,
    // und die `script` und `style` Attribute darin korrekt gesetzt sind,
    // würde WordPress diesen Block automatisch registrieren.
    //
    // Für die PHP-Registrierung (als Fallback oder für dynamische Blöcke):
    // register_block_type( KNEIPP_PREMIUM_THEME_DIR . 'src/blocks/pillars-teaser' ); // Pfad zum Verzeichnis mit block.json

    // Manuelle Registrierung (Beispiel, falls keine block.json verwendet wird oder zusätzliche Logik nötig ist):
    /*
    $pillars_teaser_asset_file = include( $blocks_asset_path . 'pillars-teaser/index.asset.php'); // Generiert durch @wordpress/scripts
    wp_register_script(
        'kneipp-premium-pillars-teaser-editor-script',
        $blocks_asset_url . 'pillars-teaser/index.js',
        $pillars_teaser_asset_file['dependencies'],
        $pillars_teaser_asset_file['version'],
        true // im Footer
    );

    wp_register_style(
        'kneipp-premium-pillars-teaser-editor-style',
        $blocks_asset_url . 'pillars-teaser/editor.css', // Editor-spezifische Styles
        array( 'wp-edit-blocks' ),
        filemtime( $blocks_asset_path . 'pillars-teaser/editor.css' )
    );

    wp_register_style(
        'kneipp-premium-pillars-teaser-style',
        $blocks_asset_url . 'pillars-teaser/style.css', // Frontend-Styles
        array(),
        filemtime( $blocks_asset_path . 'pillars-teaser/style.css' )
    );

    register_block_type( 'kneipp-premium/pillars-teaser', array(
        'api_version'   => 3, // Für WP 6.1+
        'title'         => __( 'Kneipp Säulen Teaser', 'kneipp-petershagen-premium' ),
        'description'   => __( 'Zeigt eine Übersicht der fünf Kneipp-Säulen mit Links.', 'kneipp-petershagen-premium' ),
        'category'      => 'kneipp-premium-blocks',
        'icon'          => 'heart', // Dashicon oder SVG
        'keywords'      => [ 'kneipp', 'säulen', 'gesundheit', 'teaser' ],
        'supports'      => [
            'html'      => false, // Keine direkte HTML-Bearbeitung
            'align'     => ['wide', 'full'],
        ],
        'attributes'    => array(
            // Hier würden Attribute definiert, die der Block verwendet, z.B.:
            // 'showIcons' => array('type' => 'boolean', 'default' => true),
            // 'textAlign' => array('type' => 'string', 'default' => 'left'),
        ),
        'editor_script' => 'kneipp-premium-pillars-teaser-editor-script', // Handle des registrierten Editor-Skripts
        'editor_style'  => 'kneipp-premium-pillars-teaser-editor-style',  // Handle des registrierten Editor-Styles
        'style'         => 'kneipp-premium-pillars-teaser-style',         // Handle des registrierten Frontend-Styles
        // 'render_callback' => 'kneipp_premium_render_pillars_teaser_block', // Für dynamische Blöcke
    ) );
    */

    // Hinweis: Für die tatsächliche Funktion nativer Blöcke sind die entsprechenden JS-Dateien
    // und ein Build-Prozess (z.B. mit @wordpress/scripts) notwendig, um die `index.js`, `editor.css`, `style.css`
    // und die `index.asset.php` (für Abhängigkeiten und Version) zu generieren.
    // Der obige Code ist eine Skizze der PHP-seitigen Registrierung.
    //
    // Der modernere Weg ist, `block.json` Dateien für jeden Block zu erstellen.
    // WordPress kann diese dann automatisch erkennen und registrieren.
    // Beispiel-Struktur für einen Block mit `block.json`:
    // /theme-root/
    //   /src/blocks/
    //     /pillars-teaser/
    //       - block.json
    //       - index.js (entry point for editor script)
    //       - edit.js
    //       - save.js (or render.php for dynamic blocks)
    //       - style.scss (frontend styles)
    //       - editor.scss (editor only styles)
    //
    // Die `block.json` würde dann Pfade zu den kompilierten Assets enthalten.
    // register_block_type( KNEIPP_PREMIUM_THEME_DIR . 'src/blocks/pillars-teaser/block.json' );
    // Oder, wenn die kompilierten Dateien in /assets/blocks/ liegen:
    // register_block_type( KNEIPP_PREMIUM_THEME_DIR . 'assets/blocks/pillars-teaser/block.json' );
    // Besser noch, WordPress scannt das /blocks Verzeichnis automatisch, wenn es im Theme-Root liegt.

    // Für dieses Konzept gehen wir davon aus, dass `block.json` Dateien verwendet werden
    // und der Build-Prozess die Assets korrekt aufbereitet.
    // Die Registrierung erfolgt dann oft automatisch oder durch explizites Laden der `block.json`.
    // Beispiel:
    // register_block_type_from_metadata( KNEIPP_PREMIUM_THEME_DIR . 'path/to/your-block/block.json' );

}
add_action( 'init', 'kneipp_premium_register_custom_blocks' );


/**
 * Beispiel für eine Render-Callback-Funktion für einen dynamischen Block.
 * (Wird nur benötigt, wenn der Block in JS `save: () => null` zurückgibt und
 *  in `register_block_type` ein `render_callback` definiert ist.)
 */
/*
function kneipp_premium_render_pillars_teaser_block( $attributes, $content, $block ) {
    // $attributes: Attribute des Blocks
    // $content: Innerer Inhalt des Blocks (wenn <InnerBlocks /> verwendet wird)
    // $block: Vollständiges Block-Objekt

    $output = '<div class="wp-block-kneipp-premium-pillars-teaser">';
    // Logik, um die 5 Säulen darzustellen (z.B. aus Taxonomie laden)
    $pillars_terms = get_terms( array(
        'taxonomy' => 'kneipp_pillar', // Unsere Taxonomie für die Säulen
        'hide_empty' => false,
        'orderby' => 'name', // Oder eine benutzerdefinierte Reihenfolge
        'order' => 'ASC',
    ) );

    if ( ! is_wp_error( $pillars_terms ) && ! empty( $pillars_terms ) ) {
        $output .= '<div class="pillars-grid">';
        foreach ( $pillars_terms as $pillar ) {
            $pillar_link = get_term_link( $pillar );
            $output .= '<div class="pillar-item">';
            // Hier Icon oder Bild hinzufügen (z.B. aus Term-Meta oder fest definiert)
            // $icon_url = get_term_meta( $pillar->term_id, 'pillar_icon_url', true );
            // if ( $icon_url ) {
            //    $output .= '<img src="' . esc_url( $icon_url ) . '" alt="' . esc_attr( $pillar->name ) . '" class="pillar-icon">';
            // } else {
            //    $output .= '<span class="pillar-icon-placeholder"></span>'; // Fallback Icon
            // }
            $output .= '<h3><a href="' . esc_url( $pillar_link ) . '">' . esc_html( $pillar->name ) . '</a></h3>';
            if ( ! empty( $pillar->description ) ) {
                $output .= '<p>' . esc_html( $pillar->description ) . '</p>';
            }
            $output .= '<a href="' . esc_url( $pillar_link ) . '" class="pillar-link">' . __( 'Mehr erfahren', 'kneipp-petershagen-premium' ) . '</a>';
            $output .= '</div>'; // .pillar-item
        }
        $output .= '</div>'; // .pillars-grid
    } else {
        $output .= '<p>' . __( 'Kneipp-Säulen konnten nicht geladen werden.', 'kneipp-petershagen-premium' ) . '</p>';
    }

    $output .= '</div>'; // .wp-block-kneipp-premium-pillars-teaser
    return $output;
}
*/

// Es ist wichtig, dass die Handles für Skripte und Stile in `register_block_type`
// mit denen in `wp_register_script` und `wp_register_style` übereinstimmen,
// oder dass `block.json` verwendet wird, das dies intern verwaltet.
?>
