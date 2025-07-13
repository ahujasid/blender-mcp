<?php
/**
 * Das Template für die Anzeige einzelner Beiträge (single posts).
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/#single-post
 *
 * @package Kneippverein_Petershagen_Premium
 */

get_header();
?>

	<?php
	/* Start the Loop */
	while ( have_posts() ) :
		the_post();

		// Versucht, ein spezifisches Template für den Post Type zu laden, z.B. parts/content-single-post.php
		// oder parts/content-single-kurs.php (wenn CPT 'kurs' ist).
		// Fallback ist parts/content-single.php
		get_template_part( 'parts/content', 'single-' . get_post_type() );


		// Beitragsnavigation (Vorheriger/Nächster Beitrag)
		the_post_navigation(
			array(
				'prev_text' => '<span class="nav-subtitle">' . esc_html__( 'Vorheriger:', 'kneipp-petershagen-premium' ) . '</span> <span class="nav-title">%title</span>',
				'next_text' => '<span class="nav-subtitle">' . esc_html__( 'Nächster:', 'kneipp-petershagen-premium' ) . '</span> <span class="nav-title">%title</span>',
				'screen_reader_text' => __( 'Beitragsnavigation', 'kneipp-petershagen-premium' ),
			)
		);

		// Wenn Kommentare für den Beitrag aktiviert sind oder wir mindestens einen Kommentar haben, lade das Kommentar-Template.
		if ( comments_open() || get_comments_number() ) :
			comments_template(); // Lädt comments.php oder parts/comments-template.php
		endif;

	endwhile; // End of the loop.
	?>

<?php
// get_sidebar(); // Optional: Falls eine Sidebar benötigt wird
get_footer();
?>
