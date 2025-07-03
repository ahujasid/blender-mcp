<?php
/**
 * Registrierung von Custom Post Types.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_register_cpts' ) ) :
	/**
	 * Registriert die Custom Post Types des Themes.
	 */
	function kneipp_premium_register_cpts() {

		// CPT: Kurse
		$course_labels = array(
			'name'                  => _x( 'Kurse', 'Post Type General Name', 'kneipp-petershagen-premium' ),
			'singular_name'         => _x( 'Kurs', 'Post Type Singular Name', 'kneipp-petershagen-premium' ),
			'menu_name'             => __( 'Kurse', 'kneipp-petershagen-premium' ),
			'name_admin_bar'        => __( 'Kurs', 'kneipp-petershagen-premium' ),
			'archives'              => __( 'Kursarchiv', 'kneipp-petershagen-premium' ),
			'attributes'            => __( 'Kurs-Attribute', 'kneipp-petershagen-premium' ),
			'parent_item_colon'     => __( 'Übergeordneter Kurs:', 'kneipp-petershagen-premium' ),
			'all_items'             => __( 'Alle Kurse', 'kneipp-petershagen-premium' ),
			'add_new_item'          => __( 'Neuen Kurs erstellen', 'kneipp-petershagen-premium' ),
			'add_new'               => __( 'Erstellen', 'kneipp-petershagen-premium' ),
			'new_item'              => __( 'Neuer Kurs', 'kneipp-petershagen-premium' ),
			'edit_item'             => __( 'Kurs bearbeiten', 'kneipp-petershagen-premium' ),
			'update_item'           => __( 'Kurs aktualisieren', 'kneipp-petershagen-premium' ),
			'view_item'             => __( 'Kurs ansehen', 'kneipp-petershagen-premium' ),
			'view_items'            => __( 'Kurse ansehen', 'kneipp-petershagen-premium' ),
			'search_items'          => __( 'Kurse suchen', 'kneipp-petershagen-premium' ),
			'not_found'             => __( 'Keine Kurse gefunden', 'kneipp-petershagen-premium' ),
			'not_found_in_trash'    => __( 'Keine Kurse im Papierkorb gefunden', 'kneipp-petershagen-premium' ),
			'featured_image'        => __( 'Kursbild', 'kneipp-petershagen-premium' ),
			'set_featured_image'    => __( 'Kursbild festlegen', 'kneipp-petershagen-premium' ),
			'remove_featured_image' => __( 'Kursbild entfernen', 'kneipp-petershagen-premium' ),
			'use_featured_image'    => __( 'Als Kursbild verwenden', 'kneipp-petershagen-premium' ),
			'insert_into_item'      => __( 'In Kurs einfügen', 'kneipp-petershagen-premium' ),
			'uploaded_to_this_item' => __( 'Zu diesem Kurs hochgeladen', 'kneipp-petershagen-premium' ),
			'items_list'            => __( 'Kursliste', 'kneipp-petershagen-premium' ),
			'items_list_navigation' => __( 'Kurslisten-Navigation', 'kneipp-petershagen-premium' ),
			'filter_items_list'     => __( 'Kursliste filtern', 'kneipp-petershagen-premium' ),
		);
		$course_args = array(
			'label'                 => __( 'Kurs', 'kneipp-petershagen-premium' ),
			'description'           => __( 'Kursangebote des Kneippvereins', 'kneipp-petershagen-premium' ),
			'labels'                => $course_labels,
			'supports'              => array( 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields', 'revisions', 'page-attributes' ),
			'taxonomies'            => array( 'course_category', 'target_group', 'kneipp_pillar' ), // Werden in taxonomies.php registriert
			'hierarchical'          => false, // Oder true, wenn Kurse Unterkurse haben können
			'public'                => true,
			'show_ui'               => true,
			'show_in_menu'          => true,
			'menu_position'         => 5, // Unter "Beiträge"
			'menu_icon'             => 'dashicons-welcome-learn-more', // https://developer.wordpress.org/resource/dashicons/
			'show_in_admin_bar'     => true,
			'show_in_nav_menus'     => true,
			'can_export'            => true,
			'has_archive'           => 'kurse', // Slug für das Archiv, z.B. yourdomain.com/kurse/
			'exclude_from_search'   => false,
			'publicly_queryable'    => true,
			'capability_type'       => 'post', // oder 'page' oder ein eigener Capability Type
            'show_in_rest'          => true, // Wichtig für Gutenberg und REST API
            'rewrite'               => array( 'slug' => 'kurse', 'with_front' => false ), // Slug für Einzelansicht
		);
		register_post_type( 'course', $course_args );


		// CPT: Veranstaltungen
		$event_labels = array(
			'name'                  => _x( 'Veranstaltungen', 'Post Type General Name', 'kneipp-petershagen-premium' ),
			'singular_name'         => _x( 'Veranstaltung', 'Post Type Singular Name', 'kneipp-petershagen-premium' ),
			'menu_name'             => __( 'Veranstaltungen', 'kneipp-petershagen-premium' ),
			'name_admin_bar'        => __( 'Veranstaltung', 'kneipp-petershagen-premium' ),
			'archives'              => __( 'Veranstaltungsarchiv', 'kneipp-petershagen-premium' ),
			'attributes'            => __( 'Veranstaltungs-Attribute', 'kneipp-petershagen-premium' ),
			'parent_item_colon'     => __( 'Übergeordnete Veranstaltung:', 'kneipp-petershagen-premium' ),
			'all_items'             => __( 'Alle Veranstaltungen', 'kneipp-petershagen-premium' ),
			'add_new_item'          => __( 'Neue Veranstaltung erstellen', 'kneipp-petershagen-premium' ),
			'add_new'               => __( 'Erstellen', 'kneipp-petershagen-premium' ),
			'new_item'              => __( 'Neue Veranstaltung', 'kneipp-petershagen-premium' ),
			'edit_item'             => __( 'Veranstaltung bearbeiten', 'kneipp-petershagen-premium' ),
			'update_item'           => __( 'Veranstaltung aktualisieren', 'kneipp-petershagen-premium' ),
			'view_item'             => __( 'Veranstaltung ansehen', 'kneipp-petershagen-premium' ),
			'view_items'            => __( 'Veranstaltungen ansehen', 'kneipp-petershagen-premium' ),
			'search_items'          => __( 'Veranstaltungen suchen', 'kneipp-petershagen-premium' ),
			'not_found'             => __( 'Keine Veranstaltungen gefunden', 'kneipp-petershagen-premium' ),
			'not_found_in_trash'    => __( 'Keine Veranstaltungen im Papierkorb gefunden', 'kneipp-petershagen-premium' ),
			'featured_image'        => __( 'Veranstaltungsbild', 'kneipp-petershagen-premium' ),
			'set_featured_image'    => __( 'Veranstaltungsbild festlegen', 'kneipp-petershagen-premium' ),
			'remove_featured_image' => __( 'Veranstaltungsbild entfernen', 'kneipp-petershagen-premium' ),
			'use_featured_image'    => __( 'Als Veranstaltungsbild verwenden', 'kneipp-petershagen-premium' ),
			'insert_into_item'      => __( 'In Veranstaltung einfügen', 'kneipp-petershagen-premium' ),
			'uploaded_to_this_item' => __( 'Zu dieser Veranstaltung hochgeladen', 'kneipp-petershagen-premium' ),
			'items_list'            => __( 'Veranstaltungsliste', 'kneipp-petershagen-premium' ),
			'items_list_navigation' => __( 'Veranstaltungslisten-Navigation', 'kneipp-petershagen-premium' ),
			'filter_items_list'     => __( 'Veranstaltungsliste filtern', 'kneipp-petershagen-premium' ),
		);
		$event_args = array(
			'label'                 => __( 'Veranstaltung', 'kneipp-petershagen-premium' ),
			'description'           => __( 'Veranstaltungen, Termine und Events des Kneippvereins', 'kneipp-petershagen-premium' ),
			'labels'                => $event_labels,
			'supports'              => array( 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields', 'revisions' ),
			'taxonomies'            => array( 'event_type', 'target_group', 'kneipp_pillar' ), // Werden in taxonomies.php registriert
			'hierarchical'          => false,
			'public'                => true,
			'show_ui'               => true,
			'show_in_menu'          => true,
			'menu_position'         => 6, // Unter "Kurse"
			'menu_icon'             => 'dashicons-calendar-alt',
			'show_in_admin_bar'     => true,
			'show_in_nav_menus'     => true,
			'can_export'            => true,
			'has_archive'           => 'veranstaltungen', // Slug für das Archiv
			'exclude_from_search'   => false,
			'publicly_queryable'    => true,
			'capability_type'       => 'post',
            'show_in_rest'          => true,
            'rewrite'               => array( 'slug' => 'veranstaltungen', 'with_front' => false ),
		);
		register_post_type( 'event', $event_args );

		// Weitere CPTs (Rezepte, Team) können hier nach demselben Muster hinzugefügt werden.
		// Beispiel für CPT "Rezepte" (gekürzt):
		/*
		$recipe_labels = array( 'name' => _x( 'Rezepte', 'Post Type General Name', 'text_domain' ), ... );
		$recipe_args = array( 'label' => __( 'Rezept', 'text_domain' ), ..., 'menu_icon' => 'dashicons-carrot', 'has_archive' => 'rezepte', 'rewrite' => array('slug' => 'rezepte') );
		register_post_type( 'recipe', $recipe_args );
		*/

	}
endif;
add_action( 'init', 'kneipp_premium_register_cpts', 0 ); // 0 = Priorität, früh ausführen


/**
 * Setzt die Nachrichten für Custom Post Types nach dem Aktualisieren/Erstellen.
 */
function kneipp_premium_cpt_updated_messages( $messages ) {
    global $post, $post_ID;

    // Nachrichten für CPT "Kurse"
    $messages['course'] = array(
        0  => '', // Unbenutzt.
        1  => sprintf( __( 'Kurs aktualisiert. <a href="%s">Kurs ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( get_permalink( $post_ID ) ) ),
        2  => __( 'Benutzerdefiniertes Feld aktualisiert.', 'kneipp-petershagen-premium' ),
        3  => __( 'Benutzerdefiniertes Feld gelöscht.', 'kneipp-petershagen-premium' ),
        4  => __( 'Kurs aktualisiert.', 'kneipp-petershagen-premium' ),
        /* translators: %s: date and time of the revision */
        5  => isset( $_GET['revision'] ) ? sprintf( __( 'Kurs wiederhergestellt auf Revision vom %s', 'kneipp-petershagen-premium' ), wp_post_revision_title( (int) $_GET['revision'], false ) ) : false,
        6  => sprintf( __( 'Kurs veröffentlicht. <a href="%s">Kurs ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( get_permalink( $post_ID ) ) ),
        7  => __( 'Kurs gespeichert.', 'kneipp-petershagen-premium' ),
        8  => sprintf( __( 'Kurs übermittelt. <a target="_blank" href="%s">Kurs als Vorschau ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( add_query_arg( 'preview', 'true', get_permalink( $post_ID ) ) ) ),
        9  => sprintf(
            __( 'Kurs geplant für: <strong>%1$s</strong>. <a target="_blank" href="%2$s">Kurs als Vorschau ansehen</a>', 'kneipp-petershagen-premium' ),
            // translators: Publish box date format, see http://php.net/date
            date_i18n( __( 'M j, Y @ G:i', 'kneipp-petershagen-premium' ), strtotime( $post->post_date ) ),
            esc_url( get_permalink( $post_ID ) )
        ),
        10 => sprintf( __( 'Kurs-Entwurf aktualisiert. <a target="_blank" href="%s">Kurs als Vorschau ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( add_query_arg( 'preview', 'true', get_permalink( $post_ID ) ) ) ),
    );

    // Nachrichten für CPT "Veranstaltungen"
    $messages['event'] = array(
        0  => '', // Unbenutzt.
        1  => sprintf( __( 'Veranstaltung aktualisiert. <a href="%s">Veranstaltung ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( get_permalink( $post_ID ) ) ),
        2  => __( 'Benutzerdefiniertes Feld aktualisiert.', 'kneipp-petershagen-premium' ),
        3  => __( 'Benutzerdefiniertes Feld gelöscht.', 'kneipp-petershagen-premium' ),
        4  => __( 'Veranstaltung aktualisiert.', 'kneipp-petershagen-premium' ),
        5  => isset( $_GET['revision'] ) ? sprintf( __( 'Veranstaltung wiederhergestellt auf Revision vom %s', 'kneipp-petershagen-premium' ), wp_post_revision_title( (int) $_GET['revision'], false ) ) : false,
        6  => sprintf( __( 'Veranstaltung veröffentlicht. <a href="%s">Veranstaltung ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( get_permalink( $post_ID ) ) ),
        7  => __( 'Veranstaltung gespeichert.', 'kneipp-petershagen-premium' ),
        8  => sprintf( __( 'Veranstaltung übermittelt. <a target="_blank" href="%s">Veranstaltung als Vorschau ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( add_query_arg( 'preview', 'true', get_permalink( $post_ID ) ) ) ),
        9  => sprintf(
            __( 'Veranstaltung geplant für: <strong>%1$s</strong>. <a target="_blank" href="%2$s">Veranstaltung als Vorschau ansehen</a>', 'kneipp-petershagen-premium' ),
            date_i18n( __( 'M j, Y @ G:i', 'kneipp-petershagen-premium' ), strtotime( $post->post_date ) ),
            esc_url( get_permalink( $post_ID ) )
        ),
        10 => sprintf( __( 'Veranstaltungs-Entwurf aktualisiert. <a target="_blank" href="%s">Veranstaltung als Vorschau ansehen</a>', 'kneipp-petershagen-premium' ), esc_url( add_query_arg( 'preview', 'true', get_permalink( $post_ID ) ) ) ),
    );

    // Hier könnten Nachrichten für weitere CPTs folgen.

    return $messages;
}
add_filter( 'post_updated_messages', 'kneipp_premium_cpt_updated_messages' );


/**
 * Optional: Spalten für CPTs im Admin-Bereich anpassen.
 * Beispiel für CPT "Kurse"
 */
function kneipp_premium_set_course_cpt_columns($columns) {
    // Standardspalten: $columns['cb'], $columns['title'], $columns['author'], $columns['date']
    $new_columns = array(
        'cb' => $columns['cb'], // Checkbox nicht vergessen
        'title' => __( 'Kurstitel', 'kneipp-petershagen-premium' ),
        // 'kurs_saeulen' => __( 'Kneipp-Säulen', 'kneipp-petershagen-premium' ), // Beispiel für Taxonomie-Spalte
        // 'kurs_start_datum' => __( 'Startdatum', 'kneipp-petershagen-premium' ), // Beispiel für Custom Field Spalte
        'author' => __( 'Autor', 'kneipp-petershagen-premium' ),
        'date' => __( 'Datum', 'kneipp-petershagen-premium' )
    );
    return $new_columns;
}
// add_filter('manage_course_posts_columns', 'kneipp_premium_set_course_cpt_columns');

/**
 * Optional: Inhalt für benutzerdefinierte Spalten im Admin-Bereich füllen.
 * Beispiel für CPT "Kurse"
 */
/*
function kneipp_premium_custom_course_column_content($column, $post_id) {
    switch ($column) {
        case 'kurs_saeulen':
            $terms = get_the_term_list($post_id, 'kneipp_pillar', '', ', ', '');
            if (is_string($terms)) {
                echo $terms;
            } else {
                _e('Keine Säulen zugewiesen', 'kneipp-petershagen-premium');
            }
            break;
        case 'kurs_start_datum':
            $start_date = get_post_meta($post_id, 'kurs_datum_start', true); // Annahme: Custom Field Slug
            if (!empty($start_date)) {
                // Ggf. Datum formatieren: date_i18n(get_option('date_format'), strtotime($start_date))
                echo esc_html($start_date);
            } else {
                _e('N/A', 'kneipp-petershagen-premium');
            }
            break;
    }
}
*/
// add_action('manage_course_posts_custom_column', 'kneipp_premium_custom_course_column_content', 10, 2);
?>
