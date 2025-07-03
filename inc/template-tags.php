<?php
/**
 * Benutzerdefinierte Template-Tags für dieses Theme.
 *
 * Diese Datei enthält Helferfunktionen, die in den Template-Dateien verwendet werden,
 * um spezifische HTML-Markups oder Daten auszugeben, z.B. Metadaten von Beiträgen.
 *
 * @package Kneippverein_Petershagen_Premium
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'kneipp_premium_posted_on' ) ) :
	/**
	 * Gibt HTML mit Metainformationen zum Veröffentlichungsdatum des aktuellen Beitrags aus.
	 */
	function kneipp_premium_posted_on() {
		$time_string = '<time class="entry-date published updated" datetime="%1$s">%2$s</time>';
		if ( get_the_time( 'U' ) !== get_the_modified_time( 'U' ) ) {
			$time_string = '<time class="entry-date published" datetime="%1$s">%2$s</time><time class="updated screen-reader-text" datetime="%3$s">%4$s</time>';
		}

		$time_string = sprintf(
			$time_string,
			esc_attr( get_the_date( DATE_W3C ) ),
			esc_html( get_the_date() ),
			esc_attr( get_the_modified_date( DATE_W3C ) ),
			esc_html( get_the_modified_date() )
		);

		$posted_on = sprintf(
			/* translators: %s: post date. */
			esc_html_x( 'Veröffentlicht am %s', 'post date', 'kneipp-petershagen-premium' ),
			'<a href="' . esc_url( get_permalink() ) . '" rel="bookmark">' . $time_string . '</a>'
		);

		echo '<span class="posted-on">' . $posted_on . '</span>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped

	}
endif;

if ( ! function_exists( 'kneipp_premium_posted_by' ) ) :
	/**
	 * Gibt HTML mit Metainformationen zum Autor des aktuellen Beitrags aus.
	 */
	function kneipp_premium_posted_by() {
		$byline = sprintf(
			/* translators: %s: post author. */
			esc_html_x( 'von %s', 'post author', 'kneipp-petershagen-premium' ),
			'<span class="author vcard"><a class="url fn n" href="' . esc_url( get_author_posts_url( get_the_author_meta( 'ID' ) ) ) . '">' . esc_html( get_the_author() ) . '</a></span>'
		);

		echo '<span class="byline"> ' . $byline . '</span>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped

	}
endif;

if ( ! function_exists( 'kneipp_premium_entry_footer' ) ) :
	/**
	 * Gibt HTML mit Metainformationen für den Footer-Bereich eines Beitrags aus.
	 * (Kategorien, Tags und Kommentarlink).
	 */
	function kneipp_premium_entry_footer() {
		// Verbirgt Kategorie und Tag-Text für Seiten.
		if ( 'post' === get_post_type() ) {
			/* translators: used between list items, there is a space after the comma */
			$categories_list = get_the_category_list( esc_html__( ', ', 'kneipp-petershagen-premium' ) );
			if ( $categories_list ) {
				/* translators: 1: list of categories. */
				printf( '<span class="cat-links">' . esc_html__( 'Veröffentlicht in %1$s', 'kneipp-petershagen-premium' ) . '</span>', $categories_list ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
			}

			/* translators: used between list items, there is a space after the comma */
			$tags_list = get_the_tag_list( '', esc_html_x( ', ', 'list item separator', 'kneipp-petershagen-premium' ) );
			if ( $tags_list ) {
				/* translators: 1: list of tags. */
				printf( '<span class="tags-links">' . esc_html__( 'Verschlagwortet mit %1$s', 'kneipp-petershagen-premium' ) . '</span>', $tags_list ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
			}
		}

		if ( ! is_single() && ! post_password_required() && ( comments_open() || get_comments_number() ) ) {
			echo '<span class="comments-link">';
			comments_popup_link(
				sprintf(
					wp_kses(
						/* translators: %s: post title */
						__( 'Kommentar <span class="screen-reader-text"> zu %s</span>', 'kneipp-petershagen-premium' ),
						array(
							'span' => array(
								'class' => array(),
							),
						)
					),
					get_the_title()
				)
			);
			echo '</span>';
		}

		edit_post_link(
			sprintf(
				wp_kses(
					/* translators: %s: Name of current post. Only visible to screen readers */
					__( 'Bearbeiten <span class="screen-reader-text">%s</span>', 'kneipp-petershagen-premium' ),
					array(
						'span' => array(
							'class' => array(),
						),
					)
				),
				get_the_title()
			),
			'<span class="edit-link">',
			'</span>'
		);
	}
endif;


if ( ! function_exists( 'kneipp_premium_post_thumbnail' ) ) :
	/**
	 * Zeigt ein optionales Beitragsbild an.
	 *
	 * Hüllt das Beitragsbild in einen Anker-Tag ein, außer wenn es sich um eine Einzelansicht handelt.
	 */
	function kneipp_premium_post_thumbnail() {
		if ( post_password_required() || is_attachment() || ! has_post_thumbnail() ) {
			return;
		}

		if ( is_singular() ) :
			?>
			<div class="post-thumbnail">
				<?php the_post_thumbnail( 'post-thumbnail' ); // 'post-thumbnail' ist eine Standardgröße, kann auch 'large', 'medium' oder eine eigene sein ?>
			</div><!-- .post-thumbnail -->
		<?php else : ?>
			<a class="post-thumbnail" href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
				<?php
					the_post_thumbnail(
						'post-thumbnail', // 'post-thumbnail', 'medium', 'large' oder eigene Größe
						array(
							'alt' => the_title_attribute(
								array(
									'echo' => false,
								)
							),
						)
					);
				?>
			</a>
		<?php
		endif; // End is_singular().
	}
endif;


if ( ! function_exists( 'kneipp_premium_comment_form_defaults' ) ) :
    /**
     * Filtert die Standardargumente des Kommentarformulars.
     *
     * @param array $defaults Die Standardargumente des Kommentarformulars.
     * @return array Die modifizierten Argumente.
     */
    function kneipp_premium_comment_form_defaults( $defaults ) {
        $commenter = wp_get_current_commenter();
        $req       = get_option( 'require_name_email' );
        $aria_req  = ( $req ? " aria-required='true'" : '' );
        $html_req  = ( $req ? " required='required'" : '' );

        $defaults['fields']['author'] =
            '<p class="comment-form-author">' .
            '<label for="author">' . esc_html__( 'Name', 'kneipp-petershagen-premium' ) . ( $req ? ' <span class="required">*</span>' : '' ) . '</label> ' .
            '<input id="author" name="author" type="text" value="' . esc_attr( $commenter['comment_author'] ) . '" size="30" maxlength="245"' . $aria_req . $html_req . ' /></p>';

        $defaults['fields']['email'] =
            '<p class="comment-form-email"><label for="email">' . esc_html__( 'E-Mail', 'kneipp-petershagen-premium' ) . ( $req ? ' <span class="required">*</span>' : '' ) . '</label> ' .
            '<input id="email" name="email" type="email" value="' . esc_attr( $commenter['comment_author_email'] ) . '" size="30" maxlength="100" aria-describedby="email-notes"' . $aria_req . $html_req . ' /></p>';

        $defaults['fields']['url'] =
            '<p class="comment-form-url"><label for="url">' . esc_html__( 'Website', 'kneipp-petershagen-premium' ) . '</label> ' .
            '<input id="url" name="url" type="url" value="' . esc_attr( $commenter['comment_author_url'] ) . '" size="30" maxlength="200" /></p>';

        $defaults['comment_field'] =
            '<p class="comment-form-comment"><label for="comment">' . esc_html_x( 'Kommentar', 'noun', 'kneipp-petershagen-premium' ) . '</label>' .
            '<textarea id="comment" name="comment" cols="45" rows="8" maxlength="65525" required="required"></textarea></p>';

        // Cookies Consent Checkbox (DSGVO-konform)
        $defaults['fields']['cookies'] = '<p class="comment-form-cookies-consent"><input id="wp-comment-cookies-consent" name="wp-comment-cookies-consent" type="checkbox" value="yes"' . ( empty( $commenter['comment_author_email'] ) ? '' : ' checked="checked"' ) . ' />' .
                                        '<label for="wp-comment-cookies-consent">' . esc_html__( 'Meinen Namen, E-Mail und Website in diesem Browser für meinen nächsten Kommentar speichern.', 'kneipp-petershagen-premium' ) . '</label></p>';


        $defaults['title_reply'] = esc_html__( 'Schreibe einen Kommentar', 'kneipp-petershagen-premium' );
        $defaults['title_reply_to'] = esc_html__( 'Antworte auf %s', 'kneipp-petershagen-premium' );
        $defaults['cancel_reply_link'] = esc_html__( 'Antwort abbrechen', 'kneipp-petershagen-premium' );
        $defaults['label_submit'] = esc_html__( 'Kommentar abschicken', 'kneipp-petershagen-premium' );

        return $defaults;
    }
endif;
add_filter( 'comment_form_defaults', 'kneipp_premium_comment_form_defaults' );


// Weitere Template-Tags könnten sein:
// - Paginierung für Beiträge/Archive (obwohl the_posts_pagination() oft ausreicht)
// - Breadcrumbs-Navigation
// - Social Sharing Links
// - Funktionen zur Anzeige von Custom Fields
// - Spezifische Ausgabeformate für Custom Post Types
?>
