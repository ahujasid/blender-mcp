<?php
/**
 * Das Haupt-Template (Fallback).
 *
 * Dies ist das generischste Template in einer WordPress-Installation und eines der beiden
 * benötigten Dateien für ein Theme (das andere ist style.css).
 * Es wird verwendet, um eine Seite anzuzeigen, wenn kein spezifischeres Template gefunden wird.
 * Z.B. wird es für die Blog-Startseite verwendet, wenn keine home.php existiert.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/
 *
 * @package Kneippverein_Petershagen_Premium
 */

get_header();
?>

	<?php if ( is_home() && ! is_front_page() ) : ?>
		<header class="page-header">
			<h1 class="page-title screen-reader-text"><?php single_post_title(); ?></h1>
		</header>
	<?php endif; ?>

	<?php
	if ( have_posts() ) :

		/* Start the Loop */
		while ( have_posts() ) :
			the_post();

			/*
			 * Binde das content-Format spezifische Template ein.
			 * Wenn du content-___.php (z.B. content-gallery.php) erstellen möchtest,
			 * dann nutze get_post_format_string() anstelle von get_post_type().
			 * Wir verwenden hier einen generischen Part für den Anfang.
			 */
			get_template_part( 'parts/content', get_post_type() ?: 'excerpt' ); // Lädt parts/content-excerpt.php oder parts/content.php

		endwhile;

		// Paginierung
		the_posts_pagination(
			array(
				'prev_text' => '<span class="screen-reader-text">' . __( 'Vorherige Seite', 'kneipp-petershagen-premium' ) . '</span><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"></path></svg>',
				'next_text' => '<span class="screen-reader-text">' . __( 'Nächste Seite', 'kneipp-petershagen-premium' ) . '</span><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"></path></svg>',
				'screen_reader_text' => __( 'Beitragsnavigation', 'kneipp-petershagen-premium' ),
			)
		);

	else :

		get_template_part( 'parts/content', 'none' ); // Lädt parts/content-none.php

	endif;
	?>

<?php
// get_sidebar(); // Optional: Falls eine Sidebar benötigt wird
get_footer();
?>
