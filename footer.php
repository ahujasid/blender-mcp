<?php
/**
 * Der Footer für unser Theme.
 *
 * Diese Datei beinhaltet den schließenden Teil des #content Divs und alles danach,
 * typischerweise Copyright-Informationen und den Aufruf von wp_footer().
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package Kneippverein_Petershagen_Premium
 */
?>
			</main><!-- #main -->
		</div><!-- .container -->
	</div><!-- #content -->

	<footer id="colophon" class="site-footer" role="contentinfo">
		<div class="site-info">
			<div class="container"> <?php // Container für das Layout ?>
				<p>
					&copy; <?php echo esc_html( date_i18n( 'Y' ) ); ?>
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php bloginfo( 'name' ); ?></a>.
					<?php
					/* translators: %s: CMS name, i.e. WordPress. */
					printf( esc_html__( 'Stolz präsentiert von %s.', 'kneipp-petershagen-premium' ), '<a href="https://wordpress.org/" target="_blank" rel="noopener noreferrer">WordPress</a>' );
					?>
					<span class="sep"> | </span>
					<?php
					/* translators: 1: Theme name, 2: Theme author. */
					printf( esc_html__( 'Theme: %1$s von %2$s.', 'kneipp-petershagen-premium' ), 'Kneippverein Petershagen Premium', '<a href="[IHRE_AUTOR_URL_HIER]" target="_blank" rel="noopener noreferrer">[Ihr Name/Agenturname]</a>' );
					?>
				</p>
				<?php if ( has_nav_menu( 'footer' ) ) : ?>
					<nav class="footer-navigation" aria-label="<?php esc_attr_e( 'Footer Menü', 'kneipp-petershagen-premium' ); ?>">
						<?php
						wp_nav_menu(
							array(
								'theme_location' => 'footer',
								'menu_class'     => 'footer-menu',
								'depth'          => 1,
                                'container'      => false,
							)
						);
						?>
					</nav><!-- .footer-navigation -->
				<?php endif; ?>

				<?php
				// Platz für Footer-Widgets, falls im Customizer oder Theme-Optionen aktiviert
				if ( is_active_sidebar( 'footer-1' ) ) {
					dynamic_sidebar( 'footer-1' );
				}
				?>
			</div><!-- .container -->
		</div><!-- .site-info -->
	</footer><!-- #colophon -->
</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>
