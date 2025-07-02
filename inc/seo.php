<?php
/**
 * SEO-bezogene Funktionen und Anpassungen für das Theme.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_breadcrumbs' ) ) :
	/**
	 * Zeigt eine Breadcrumb-Navigation an.
	 *
	 * Optionen:
	 * - Kann mit Yoast SEO oder Rank Math Breadcrumbs integriert werden, falls diese aktiv sind.
	 * - Bietet eine eigene Fallback-Implementierung.
	 * - Gibt Schema.org BreadcrumbList Markup aus.
	 *
	 * @param array $args Argumente zur Anpassung der Breadcrumbs.
	 */
	function kneipp_premium_breadcrumbs( $args = array() ) {
		if ( ! is_front_page() ) { // Nicht auf der Startseite anzeigen

			// Standardargumente
			$defaults = array(
				'home_text'         => __( 'Startseite', 'kneipp-petershagen-premium' ),
				'separator'         => '&nbsp;&raquo;&nbsp;', // Separator zwischen den Elementen
				'container_before'  => '<nav class="breadcrumbs" aria-label="' . esc_attr__( 'Brotkrümelnavigation', 'kneipp-petershagen-premium' ) . '"><ol itemscope itemtype="https://schema.org/BreadcrumbList">',
				'container_after'   => '</ol></nav>',
				'item_before'       => '<li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">',
				'item_after'        => '</li>',
				'show_current'      => true, // Aktuelle Seite anzeigen?
				'current_text'      => '',   // Wird durch den Titel der aktuellen Seite ersetzt
				'show_on_home'      => false, // Breadcrumbs auf der Startseite anzeigen?
			);
			$args = wp_parse_args( $args, $defaults );

			// Integration mit Yoast SEO Breadcrumbs (bevorzugt, wenn aktiv)
			if ( function_exists( 'yoast_breadcrumb' ) ) {
				// Yoast gibt bereits <nav> und Schema.org Markup aus, daher nur den Container anpassen, falls nötig.
				// Oder einfach Yoast machen lassen und diese Funktion nicht aufrufen, wenn Yoast aktiv ist.
				// Für dieses Beispiel gehen wir davon aus, dass wir Yoast nicht überschreiben,
				// sondern unsere eigene Logik als Fallback haben oder wenn Yoast Breadcrumbs deaktiviert sind.
				// Wenn Sie Yoast nutzen wollen:
				// yoast_breadcrumb( '<nav class="breadcrumbs" aria-label="' . esc_attr__( 'Brotkrümelnavigation', 'kneipp-petershagen-premium' ) . '">','</nav>' );
				// return;
			}

			// Integration mit Rank Math Breadcrumbs (bevorzugt, wenn aktiv und Yoast nicht)
			if ( function_exists( 'rank_math_the_breadcrumb' ) && ! function_exists( 'yoast_breadcrumb' ) ) {
				// rank_math_the_breadcrumb();
				// return;
			}


			// Eigene Breadcrumb-Logik
			global $post;
			$items = array();
			$position = 1;

			// Startseite Link
			$items[] = array(
				'url'  => home_url( '/' ),
				'text' => $args['home_text'],
			);

			if ( is_home() && ! is_front_page() ) { // Blog-Seite (Beitragsseite)
				$blog_page_id = get_option( 'page_for_posts' );
				if ( $blog_page_id ) {
					$items[] = array( 'text' => get_the_title( $blog_page_id ) );
				}
			} elseif ( is_category() ) {
				$cat_obj = get_queried_object();
				if ( $cat_obj->parent != 0 ) {
					$parent_cats = get_category_parents( $cat_obj->parent, true, $args['separator'] );
					$parent_cats_array = explode( $args['separator'], rtrim( $parent_cats, $args['separator'] ) );
					foreach ( $parent_cats_array as $parent_cat_link ) {
						preg_match( '/<a href="([^"]+)">([^<]+)<\/a>/', $parent_cat_link, $matches );
                        if(isset($matches[1]) && isset($matches[2])) {
						    $items[] = array( 'url' => $matches[1], 'text' => $matches[2] );
                        }
					}
				}
				$items[] = array( 'text' => single_cat_title( '', false ) );
			} elseif ( is_tag() ) {
				$items[] = array( 'text' => single_tag_title( __( 'Archiv für Tag: ', 'kneipp-petershagen-premium' ), false ) );
			} elseif ( is_author() ) {
				$items[] = array( 'text' => get_the_author_meta( 'display_name', get_query_var( 'author' ) ) );
			} elseif ( is_day() ) {
				$items[] = array( 'url' => get_year_link( get_the_time( 'Y' ) ), 'text' => get_the_time( 'Y' ) );
				$items[] = array( 'url' => get_month_link( get_the_time( 'Y' ), get_the_time( 'm' ) ), 'text' => get_the_time( 'F' ) );
				$items[] = array( 'text' => get_the_time( 'd' ) );
			} elseif ( is_month() ) {
				$items[] = array( 'url' => get_year_link( get_the_time( 'Y' ) ), 'text' => get_the_time( 'Y' ) );
				$items[] = array( 'text' => get_the_time( 'F' ) );
			} elseif ( is_year() ) {
				$items[] = array( 'text' => get_the_time( 'Y' ) );
			} elseif ( is_search() ) {
				$items[] = array( 'text' => __( 'Suchergebnisse für: ', 'kneipp-petershagen-premium' ) . '"' . get_search_query() . '"' );
			} elseif ( is_404() ) {
				$items[] = array( 'text' => __( '404 Seite nicht gefunden', 'kneipp-petershagen-premium' ) );
			} elseif ( is_singular() ) {
				$post_type = get_post_type();
				if ( $post_type != 'post' && $post_type != 'page' ) {
					$post_type_object = get_post_type_object( $post_type );
					$archive_link = get_post_type_archive_link( $post_type );
					if ( $archive_link && $post_type_object ) {
						$items[] = array( 'url' => $archive_link, 'text' => $post_type_object->labels->name );
					}
				}

				if ( $post->post_parent ) {
					$ancestors = array_reverse( get_post_ancestors( $post->ID ) );
					foreach ( $ancestors as $ancestor ) {
						$items[] = array( 'url' => get_permalink( $ancestor ), 'text' => get_the_title( $ancestor ) );
					}
				}
                // Taxonomien für CPTs (z.B. erste Kategorie eines Kurses)
                if ( 'course' === $post_type ) { // Beispiel für CPT 'course'
                    $terms = wp_get_post_terms( $post->ID, 'course_category', array( 'orderby' => 'parent', 'order' => 'DESC' ) );
                    if ( ! empty( $terms ) && ! is_wp_error( $terms ) ) {
                        $main_term = $terms[0]; // Nimm den ersten Term
                        $items[] = array( 'url' => get_term_link( $main_term ), 'text' => $main_term->name );
                    }
                }

				if ( $args['show_current'] ) {
					$items[] = array( 'text' => $args['current_text'] ?: get_the_title() );
				}
			} elseif ( is_post_type_archive() ) {
				$post_type_object = get_queried_object();
				if ( $post_type_object && isset( $post_type_object->labels->name ) ) {
					$items[] = array( 'text' => $post_type_object->labels->name );
				}
			} elseif ( is_tax() ) {
				$term = get_queried_object();
				$items[] = array( 'text' => $term->name );
			}


			// Output der Breadcrumbs
			echo $args['container_before'];
			foreach ( $items as $item ) {
				echo $args['item_before'];
				if ( ! empty( $item['url'] ) ) {
					echo '<a itemprop="item" href="' . esc_url( $item['url'] ) . '"><span itemprop="name">' . esc_html( $item['text'] ) . '</span></a>';
				} else {
					echo '<span itemprop="name">' . esc_html( $item['text'] ) . '</span>';
				}
				echo '<meta itemprop="position" content="' . esc_attr( $position++ ) . '" />';
				echo $args['item_after'];
				if ( next( $items ) ) {
					// echo '<span class="breadcrumbs__separator">' . wp_kses_post( $args['separator'] ) . '</span>'; // Separator nicht im LI
				}
			}
			echo $args['container_after'];
		}
	}
endif;


if ( ! function_exists( 'kneipp_premium_generate_course_schema' ) ) :
    /**
     * Generiert JSON-LD Schema Markup für einen einzelnen Kurs (CPT 'course').
     * Sollte auf der Einzelansicht eines Kurses aufgerufen werden.
     *
     * @param WP_Post|int $post Der Post-Objekt oder die Post-ID des Kurses.
     * @return string Das JSON-LD Script Tag oder leerer String.
     */
    function kneipp_premium_generate_course_schema( $post = null ) {
        if ( is_null( $post ) ) {
            $post = get_post();
        } elseif ( is_numeric( $post ) ) {
            $post = get_post( $post );
        }

        if ( ! $post || 'course' !== $post->post_type ) {
            return '';
        }

        // Benötigte Custom Fields für den Kurs (Beispiel-Slugs)
        $start_date = get_post_meta( $post->ID, 'kurs_datum_start', true ); // YYYY-MM-DD
        $end_date   = get_post_meta( $post->ID, 'kurs_datum_ende', true );   // YYYY-MM-DD
        $location_name = get_post_meta( $post->ID, 'kurs_ort', true );
        $price = get_post_meta( $post->ID, 'kurs_preis', true ); // z.B. "50"
        $price_currency = 'EUR'; // Oder aus Optionen holen

        $schema = array(
            '@context'    => 'https://schema.org',
            '@type'       => 'CourseInstance', // Oder 'Event' wenn es besser passt
            'name'        => get_the_title( $post ),
            'description' => wp_strip_all_tags( get_the_excerpt( $post ) ?: $post->post_content ),
            'url'         => get_permalink( $post ),
        );

        if ( has_post_thumbnail( $post ) ) {
            $schema['image'] = get_the_post_thumbnail_url( $post, 'large' );
        }

        if ( $start_date ) {
            // Ggf. Uhrzeit hinzufügen, wenn vorhanden (z.B. aus 'kurs_zeit' Feld)
            // $schema['startDate'] = date( DATE_ISO8601, strtotime( $start_date . ' ' . $kurs_zeit_start ) );
            $schema['startDate'] = $start_date; // ISO 8601 Format (YYYY-MM-DD)
        }
        if ( $end_date ) {
            $schema['endDate'] = $end_date;
        }

        if ( $location_name ) {
            $schema['location'] = array(
                '@type' => 'Place',
                'name'  => $location_name,
                // 'address' => array( '@type' => 'PostalAddress', 'streetAddress' => '...', ... ) // Detailliertere Adresse
            );
        }

        if ( $price ) {
            $schema['offers'] = array(
                '@type'         => 'Offer',
                'price'         => $price,
                'priceCurrency' => $price_currency,
                'url'           => get_permalink( $post ), // Link zur Anmeldeseite
                'availability'  => 'https://schema.org/InStock', // Oder anderer Status
            );
        }

        // Anbieter (Organisation)
        $schema['organizer'] = array(
            '@type' => 'Organization',
            'name'  => get_bloginfo('name'),
            'url'   => home_url('/')
        );
        // Kursleiter (Instructor)
        // $kurs_leiter = get_post_meta( $post->ID, 'kurs_leiter', true );
        // if($kurs_leiter){
        //    $schema['instructor'] = array(
        //        '@type' => 'Person',
        //        'name' => $kurs_leiter
        //    );
        // }


        if ( ! empty( $schema ) ) {
            return '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT ) . '</script>';
        }
        return '';
    }
endif;

/**
 * Fügt das JSON-LD Schema für Kurse in den Head der Einzelseiten ein.
 */
function kneipp_premium_add_course_schema_to_head() {
    if ( is_singular( 'course' ) ) {
        echo kneipp_premium_generate_course_schema();
    }
}
add_action( 'wp_head', 'kneipp_premium_add_course_schema_to_head' );


// Weitere Funktionen für spezifische JSON-LD Skripte (Veranstaltungen, Organisation etc.)
// könnten hier folgen oder von SEO-Plugins übernommen werden.

// Beispiel: Organisation Schema (oft schon von Yoast abgedeckt)
/*
function kneipp_premium_generate_organization_schema() {
    $schema = array(
        '@context' => 'https://schema.org',
        '@type'    => 'Organization', // Oder 'NGO' für einen Verein
        'name'     => get_bloginfo( 'name' ),
        'url'      => home_url( '/' ),
    );
    if ( has_custom_logo() ) {
        $logo_id = get_theme_mod( 'custom_logo' );
        $logo    = wp_get_attachment_image_src( $logo_id, 'full' );
        if ( $logo ) {
            $schema['logo'] = $logo[0];
        }
    }
    // Weitere Infos: address, contactPoint, sameAs (Social Media) etc.
    return '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT ) . '</script>';
}

function kneipp_premium_add_organization_schema_to_head() {
    if ( is_front_page() ) { // Nur auf der Startseite ausgeben
        echo kneipp_premium_generate_organization_schema();
    }
}
add_action( 'wp_head', 'kneipp_premium_add_organization_schema_to_head' );
*/

?>
