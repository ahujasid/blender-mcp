<?php
/**
 * Registrierung von Custom Taxonomies.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_register_taxonomies' ) ) :
	/**
	 * Registriert die Custom Taxonomies des Themes.
	 */
	function kneipp_premium_register_taxonomies() {

		// Taxonomie: Kurs-Kategorien (für CPT "Kurse")
		$course_category_labels = array(
			'name'                       => _x( 'Kurs-Kategorien', 'Taxonomy General Name', 'kneipp-petershagen-premium' ),
			'singular_name'              => _x( 'Kurs-Kategorie', 'Taxonomy Singular Name', 'kneipp-petershagen-premium' ),
			'menu_name'                  => __( 'Kurs-Kategorien', 'kneipp-petershagen-premium' ),
			'all_items'                  => __( 'Alle Kurs-Kategorien', 'kneipp-petershagen-premium' ),
			'parent_item'                => __( 'Übergeordnete Kurs-Kategorie', 'kneipp-petershagen-premium' ),
			'parent_item_colon'          => __( 'Übergeordnete Kurs-Kategorie:', 'kneipp-petershagen-premium' ),
			'new_item_name'              => __( 'Neue Kurs-Kategorie', 'kneipp-petershagen-premium' ),
			'add_new_item'               => __( 'Neue Kurs-Kategorie hinzufügen', 'kneipp-petershagen-premium' ),
			'edit_item'                  => __( 'Kurs-Kategorie bearbeiten', 'kneipp-petershagen-premium' ),
			'update_item'                => __( 'Kurs-Kategorie aktualisieren', 'kneipp-petershagen-premium' ),
			'view_item'                  => __( 'Kurs-Kategorie ansehen', 'kneipp-petershagen-premium' ),
			'separate_items_with_commas' => __( 'Kurs-Kategorien mit Kommas trennen', 'kneipp-petershagen-premium' ),
			'add_or_remove_items'        => __( 'Kurs-Kategorien hinzufügen oder entfernen', 'kneipp-petershagen-premium' ),
			'choose_from_most_used'      => __( 'Aus den meistverwendeten Kurs-Kategorien wählen', 'kneipp-petershagen-premium' ),
			'popular_items'              => __( 'Beliebte Kurs-Kategorien', 'kneipp-petershagen-premium' ),
			'search_items'               => __( 'Kurs-Kategorien suchen', 'kneipp-petershagen-premium' ),
			'not_found'                  => __( 'Keine Kurs-Kategorien gefunden', 'kneipp-petershagen-premium' ),
			'no_terms'                   => __( 'Keine Kurs-Kategorien', 'kneipp-petershagen-premium' ),
			'items_list'                 => __( 'Kurs-Kategorien-Liste', 'kneipp-petershagen-premium' ),
			'items_list_navigation'      => __( 'Kurs-Kategorien-Listen-Navigation', 'kneipp-petershagen-premium' ),
		);
		$course_category_args = array(
			'labels'                     => $course_category_labels,
			'hierarchical'               => true, // Wie Kategorien (true) oder Tags (false)
			'public'                     => true,
			'show_ui'                    => true,
			'show_admin_column'          => true, // Zeigt die Taxonomie-Spalte in der CPT-Übersicht
			'show_in_nav_menus'          => true,
			'show_tagcloud'              => true,
            'show_in_rest'               => true, // Wichtig für Gutenberg und REST API
            'rewrite'                    => array( 'slug' => 'kurs-kategorie', 'with_front' => false ),
		);
		register_taxonomy( 'course_category', array( 'course' ), $course_category_args ); // Mit CPT 'course' verbinden


		// Taxonomie: Kneipp-Säulen (für CPTs "Kurse", "Rezepte", "Beiträge")
		$pillar_labels = array(
			'name'                       => _x( 'Kneipp-Säulen', 'Taxonomy General Name', 'kneipp-petershagen-premium' ),
			'singular_name'              => _x( 'Kneipp-Säule', 'Taxonomy Singular Name', 'kneipp-petershagen-premium' ),
			'menu_name'                  => __( 'Kneipp-Säulen', 'kneipp-petershagen-premium' ),
			'all_items'                  => __( 'Alle Kneipp-Säulen', 'kneipp-petershagen-premium' ),
			'new_item_name'              => __( 'Neue Kneipp-Säule', 'kneipp-petershagen-premium' ),
			'add_new_item'               => __( 'Neue Kneipp-Säule hinzufügen', 'kneipp-petershagen-premium' ),
			'edit_item'                  => __( 'Kneipp-Säule bearbeiten', 'kneipp-petershagen-premium' ),
			'update_item'                => __( 'Kneipp-Säule aktualisieren', 'kneipp-petershagen-premium' ),
			'view_item'                  => __( 'Kneipp-Säule ansehen', 'kneipp-petershagen-premium' ),
			'separate_items_with_commas' => __( 'Säulen mit Kommas trennen', 'kneipp-petershagen-premium' ),
			'add_or_remove_items'        => __( 'Säulen hinzufügen oder entfernen', 'kneipp-petershagen-premium' ),
			'choose_from_most_used'      => __( 'Aus den meistverwendeten Säulen wählen', 'kneipp-petershagen-premium' ),
			'popular_items'              => __( 'Beliebte Säulen', 'kneipp-petershagen-premium' ),
			'search_items'               => __( 'Säulen suchen', 'kneipp-petershagen-premium' ),
			'not_found'                  => __( 'Keine Säulen gefunden', 'kneipp-petershagen-premium' ),
			'no_terms'                   => __( 'Keine Säulen', 'kneipp-petershagen-premium' ),
			'items_list'                 => __( 'Säulen-Liste', 'kneipp-petershagen-premium' ),
			'items_list_navigation'      => __( 'Säulen-Listen-Navigation', 'kneipp-petershagen-premium' ),
		);
		$pillar_args = array(
			'labels'                     => $pillar_labels,
			'hierarchical'               => false, // Eher wie Tags, da es eine feste, flache Liste der 5 Säulen ist
			'public'                     => true,
			'show_ui'                    => true,
			'show_admin_column'          => true,
			'show_in_nav_menus'          => true,
			'show_tagcloud'              => false, // Eine Tag-Cloud der 5 Säulen ist meist nicht sinnvoll
            'show_in_rest'               => true,
            'rewrite'                    => array( 'slug' => 'kneipp-saeule', 'with_front' => false ),
		);
		// Mit CPTs 'course', 'event', 'recipe' (falls vorhanden) und 'post' verbinden
		register_taxonomy( 'kneipp_pillar', array( 'course', 'event', 'post' /*, 'recipe' */ ), $pillar_args );


        // Taxonomie: Veranstaltungs-Typen (für CPT "Veranstaltungen")
		$event_type_labels = array(
			'name'                       => _x( 'Veranstaltungs-Typen', 'Taxonomy General Name', 'kneipp-petershagen-premium' ),
			'singular_name'              => _x( 'Veranstaltungs-Typ', 'Taxonomy Singular Name', 'kneipp-petershagen-premium' ),
			'menu_name'                  => __( 'Veranstaltungs-Typen', 'kneipp-petershagen-premium' ),
			'all_items'                  => __( 'Alle Typen', 'kneipp-petershagen-premium' ),
			'parent_item'                => __( 'Übergeordneter Typ', 'kneipp-petershagen-premium' ),
			// ... weitere Labels analog zu oben ...
			'search_items'               => __( 'Typen suchen', 'kneipp-petershagen-premium' ),
			'not_found'                  => __( 'Keine Typen gefunden', 'kneipp-petershagen-premium' ),
		);
		$event_type_args = array(
			'labels'                     => $event_type_labels,
			'hierarchical'               => true, // z.B. Vortrag, Workshop als Unterpunkte von "Bildung"
			'public'                     => true,
			'show_ui'                    => true,
			'show_admin_column'          => true,
			'show_in_nav_menus'          => true,
			'show_tagcloud'              => true,
            'show_in_rest'               => true,
            'rewrite'                    => array( 'slug' => 'veranstaltungs-typ', 'with_front' => false ),
		);
		register_taxonomy( 'event_type', array( 'event' ), $event_type_args );


		// Weitere Taxonomien (Zielgruppen, Rezept-Kategorien) können hier nach demselben Muster hinzugefügt werden.
        // Beispiel für Taxonomie "Zielgruppen" (gekürzt):
        /*
        $target_group_labels = array( 'name' => _x( 'Zielgruppen', 'Taxonomy General Name', 'text_domain' ), ... );
        $target_group_args = array( 'labels' => $target_group_labels, 'hierarchical' => false, 'rewrite' => array( 'slug' => 'zielgruppe' ) );
        register_taxonomy( 'target_group', array( 'course', 'event' ), $target_group_args );
        */

	}
endif;
add_action( 'init', 'kneipp_premium_register_taxonomies', 0 );


/**
 * Optional: Fügt Standard-Terme für die "Kneipp-Säulen"-Taxonomie hinzu,
 * wenn das Theme aktiviert wird und die Terme noch nicht existieren.
 */
function kneipp_premium_insert_default_pillar_terms() {
    $pillars = array(
        'Wasser'    => array( 'slug' => 'wasser', 'description' => 'Die Kraft des Wassers für Gesundheit und Wohlbefinden.' ),
        'Pflanzen'  => array( 'slug' => 'pflanzen', 'description' => 'Heilpflanzen als natürliche Helfer.' ),
        'Bewegung'  => array( 'slug' => 'bewegung', 'description' => 'Regelmäßige, maßvolle Bewegung an frischer Luft.' ),
        'Ernährung' => array( 'slug' => 'ernaehrung', 'description' => 'Naturbelassene und vollwertige Kost.' ),
        'Balance'   => array( 'slug' => 'balance', 'description' => 'Innere Ordnung und seelisches Gleichgewicht.' ),
    );

    foreach ( $pillars as $pillar_name => $pillar_data ) {
        if ( ! term_exists( $pillar_name, 'kneipp_pillar' ) ) {
            wp_insert_term(
                $pillar_name,          // Der Name des Terms
                'kneipp_pillar',       // Die Taxonomie
                array(
                    'description' => $pillar_data['description'],
                    'slug'        => $pillar_data['slug'],
                )
            );
        }
    }
}
add_action( 'after_switch_theme', 'kneipp_premium_insert_default_pillar_terms' );
// Es ist oft besser, solche Initialisierungen über einen Admin-Hinweis mit Button zu steuern,
// oder sicherzustellen, dass sie nur einmal ausgeführt werden (z.B. mit einer Option).
// Für dieses Beispiel lassen wir es bei 'after_switch_theme'.
?>
