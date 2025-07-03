<?php
/**
 * Das Template für die Anzeige von Archivseiten.
 *
 * Wird für Kategorien, Tags, Autoren, Datums-basierte Archive etc. verwendet,
 * wenn kein spezifischeres Template (z.B. category.php, tag.php) vorhanden ist.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/
 *
 * @package Kneippverein_Petershagen_Premium
 */

get_header();
?>

	<?php if ( have_posts() ) : ?>

		<header class="page-header">
			<?php
				the_archive_title( '<h1 class="page-title">', '</h1>' );
				the_archive_description( '<div class="archive-description">', '</div>' );
			?>
		</header><!-- .page-header -->

		<?php
		/* Start the Loop */
		while ( have_posts() ) :
			the_post();

			/*
			 * Binde das content-Format spezifische Template ein.
			 * Wir verwenden hier einen generischen Part für den Anfang, typischerweise eine Vorschau (Excerpt).
			 */
			get_template_part( 'parts/content', get_post_type() ?: 'excerpt' ); // Lädt parts/content-excerpt.php oder parts/content.php

		endwhile;

		// Paginierung
		the_posts_pagination(
			array(
				'prev_text' => '<span class="screen-reader-text">' . __( 'Vorherige Seite', 'kneipp-petershagen-premium' ) . '</span><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"></path></svg>',
				'next_text' => '<span class="screen-reader-text">' . __( 'Nächste Seite', 'kneipp-petershagen-premium' ) . '</span><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"></path></svg>',
				'screen_reader_text' => __( 'Archivnavigation', 'kneipp-petershagen-premium' ),
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
