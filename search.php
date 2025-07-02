<?php
/**
 * Das Template für die Anzeige von Suchergebnissen.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/#search-result
 *
 * @package Kneippverein_Petershagen_Premium
 */

get_header();
?>

	<section class="search-results">
		<?php if ( have_posts() ) : ?>

			<header class="page-header">
				<h1 class="page-title">
					<?php
					/* translators: %s: search query. */
					printf( esc_html__( 'Suchergebnisse für: %s', 'kneipp-petershagen-premium' ), '<span>' . get_search_query() . '</span>' );
					?>
				</h1>
			</header><!-- .page-header -->

			<?php
			/* Start the Loop */
			while ( have_posts() ) :
				the_post();

				/**
				 * Führe die Loop für die Suchergebnisse aus.
				 * Wir verwenden hier ein Excerpt-Format.
				 */
				get_template_part( 'parts/content', 'excerpt' ); // Lädt parts/content-excerpt.php

			endwhile;

			// Paginierung
			the_posts_pagination(
				array(
					'prev_text' => '<span class="screen-reader-text">' . __( 'Vorherige Seite', 'kneipp-petershagen-premium' ) . '</span><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"></path></svg>',
					'next_text' => '<span class="screen-reader-text">' . __( 'Nächste Seite', 'kneipp-petershagen-premium' ) . '</span><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"></path></svg>',
					'screen_reader_text' => __( 'Suchergebnisnavigation', 'kneipp-petershagen-premium' ),
				)
			);

		else : ?>

			<header class="page-header">
				<h1 class="page-title"><?php esc_html_e( 'Nichts gefunden', 'kneipp-petershagen-premium' ); ?></h1>
			</header><!-- .page-header -->

			<div class="page-content">
				<p><?php esc_html_e( 'Entschuldigung, aber für Ihre Suchanfrage wurden keine Ergebnisse gefunden. Bitte versuchen Sie es mit anderen Suchbegriffen.', 'kneipp-petershagen-premium' ); ?></p>
				<?php get_search_form(); ?>
			</div><!-- .page-content -->

		<?php endif; ?>
	</section><!-- .search-results -->

<?php
// get_sidebar(); // Optional: Falls eine Sidebar benötigt wird
get_footer();
?>
