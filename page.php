<?php
/**
 * Das Template für die Anzeige aller statischen Seiten.
 *
 * Dies ist das Template, das standardmäßig für alle Seiten verwendet wird,
 * es sei denn, es wird ein spezifischeres Seiten-Template (z.B. page-slug.php oder ein
 * Custom Template via Seiteneinstellungen) zugewiesen.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/#single-page
 *
 * @package Kneippverein_Petershagen_Premium
 */

get_header();
?>

	<?php
	/* Start the Loop */
	while ( have_posts() ) :
		the_post();

		get_template_part( 'parts/content', 'page' ); // Lädt parts/content-page.php

		// Wenn Kommentare auf der Seite aktiviert sind oder wir mindestens einen Kommentar haben, lade das Kommentar-Template.
		if ( comments_open() || get_comments_number() ) :
			comments_template(); // Lädt comments.php oder parts/comments-template.php
		endif;

	endwhile; // End of the loop.
	?>

<?php
// get_sidebar(); // Optional: Falls eine Sidebar benötigt wird
get_footer();
?>
