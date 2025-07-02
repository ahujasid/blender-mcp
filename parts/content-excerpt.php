<?php
/**
 * Template Part für die Anzeige von Beitragsvorschauen (Exzerpte).
 * Wird typischerweise in Archivseiten (archive.php, index.php, search.php) verwendet.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/
 *
 * @package Kneippverein_Petershagen_Premium
 */
?>

<article id="post-<?php the_ID(); ?>" <?php post_class('entry-excerpt'); ?>>
	<header class="entry-header">
		<?php
		the_title( sprintf( '<h2 class="entry-title"><a href="%s" rel="bookmark">', esc_url( get_permalink() ) ), '</a></h2>' );

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
        <div class="post-thumbnail post-thumbnail-excerpt">
            <a href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
                <?php the_post_thumbnail( 'medium' ); // 'medium' oder eine andere passende Größe für Exzerpte ?>
            </a>
        </div>
    <?php endif; ?>

	<div class="entry-summary">
		<?php the_excerpt(); ?>
	</div><!-- .entry-summary -->

	<footer class="entry-footer">
        <a href="<?php echo esc_url( get_permalink() ); ?>" class="read-more-link">
            <?php
            printf(
                /* translators: %s: Name of current post. */
                wp_kses( __( 'Weiterlesen<span class="screen-reader-text"> "%s"</span>', 'kneipp-petershagen-premium' ), array( 'span' => array( 'class' => array() ) ) ),
                get_the_title()
            );
            ?>
        </a>
		<?php
        // Beispielhafter Template-Tag für Kategorien und Tags (muss in inc/template-tags.php erstellt werden)
        // kneipp_premium_entry_footer_excerpt();
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
