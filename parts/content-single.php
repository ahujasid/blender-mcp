<?php
/**
 * Template Part für die Anzeige einzelner Beiträge (verwendet von single.php).
 * Dies ist ein generischer Fallback, falls kein spezifischeres parts/content-single-{post_type}.php existiert.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/
 *
 * @package Kneippverein_Petershagen_Premium
 */
?>

<article id="post-<?php the_ID(); ?>" <?php post_class('entry-single'); // Zusätzliche Klasse für Styling von Einzelansichten ?>>
	<header class="entry-header">
		<?php
		if ( is_singular() ) :
			the_title( '<h1 class="entry-title">', '</h1>' );
		else :
			the_title( '<h2 class="entry-title"><a href="' . esc_url( get_permalink() ) . '" rel="bookmark">', '</a></h2>' );
		endif;

		if ( 'post' === get_post_type() ) : // Nur für Standard-Beiträge Metadaten anzeigen
			?>
			<div class="entry-meta">
				<?php
				// Beispielhafte Template-Tags für Autor und Datum (müssen in inc/template-tags.php erstellt werden)
				// kneipp_premium_posted_on();
				// kneipp_premium_posted_by();
				?>
				<span class="posted-on"><?php echo get_the_date(); ?></span>
				<span class="byline"> <?php esc_html_e('von','kneipp-petershagen-premium'); ?> <?php the_author_posts_link(); ?></span>
			</div><!-- .entry-meta -->
		<?php endif; ?>
	</header><!-- .entry-header -->

	<?php // kneipp_premium_post_thumbnail(); // Funktion, um das Beitragsbild anzuzeigen (muss in template-tags.php definiert werden) ?>
    <?php if ( has_post_thumbnail() ) : ?>
        <div class="post-thumbnail">
            <?php the_post_thumbnail( 'large' ); // 'large' oder eine andere definierte Größe ?>
        </div>
    <?php endif; ?>

	<div class="entry-content">
		<?php
		the_content(
			sprintf(
				wp_kses(
					/* translators: %s: Name of current post. Only visible to screen readers */
					__( 'Weiterlesen <span class="screen-reader-text"> "%s"</span>', 'kneipp-petershagen-premium' ),
					array(
						'span' => array(
							'class' => array(),
						),
					)
				),
				get_the_title()
			)
		);

		wp_link_pages(
			array(
				'before' => '<div class="page-links">' . esc_html__( 'Seiten:', 'kneipp-petershagen-premium' ),
				'after'  => '</div>',
			)
		);
		?>
	</div><!-- .entry-content -->

	<footer class="entry-footer">
		<?php
        // Beispielhafter Template-Tag für Kategorien und Tags (muss in inc/template-tags.php erstellt werden)
        // kneipp_premium_entry_footer();
        if ( 'post' === get_post_type() ) {
            $categories_list = get_the_category_list( esc_html__( ', ', 'kneipp-petershagen-premium' ) );
            if ( $categories_list ) {
                printf( '<span class="cat-links">' . esc_html__( 'Veröffentlicht in %1$s', 'kneipp-petershagen-premium' ) . '</span>', $categories_list ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
            }

            $tags_list = get_the_tag_list( '', esc_html_x( ', ', 'list item separator', 'kneipp-petershagen-premium' ) );
            if ( $tags_list ) {
                printf( '<span class="tags-links">' . esc_html__( 'Verschlagwortet mit %1$s', 'kneipp-petershagen-premium' ) . '</span>', $tags_list ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
            }
        }

		if ( get_edit_post_link() ) {
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
		?>
	</footer><!-- .entry-footer -->
</article><!-- #post-<?php the_ID(); ?> -->
