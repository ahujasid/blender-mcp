<?php
/**
 * Das Template für die Anzeige von 404-Fehlerseiten (Seite nicht gefunden).
 *
 * @link https://codex.wordpress.org/Creating_an_Error_404_Page
 *
 * @package Kneippverein_Petershagen_Premium
 */

get_header();
?>

	<section class="error-404 not-found">
		<header class="page-header">
			<h1 class="page-title"><?php esc_html_e( 'Seite nicht gefunden (404)', 'kneipp-petershagen-premium' ); ?></h1>
		</header><!-- .page-header -->

		<div class="page-content">
			<p><?php esc_html_e( 'Hoppla! Die Seite, die Sie suchen, konnte nicht gefunden werden. Möglicherweise wurde sie verschoben, umbenannt oder existiert nicht mehr.', 'kneipp-petershagen-premium' ); ?></p>
			<p><?php esc_html_e( 'Vielleicht hilft Ihnen eine Suche weiter?', 'kneipp-petershagen-premium' ); ?></p>

			<?php get_search_form(); ?>

			<div class="error-404-navigation">
				<h2 class="screen-reader-text"><?php esc_html_e( 'Alternative Navigation', 'kneipp-petershagen-premium' ); ?></h2>
				<p><?php esc_html_e( 'Oder versuchen Sie einen der folgenden Links:', 'kneipp-petershagen-premium' ); ?></p>
				<?php
					wp_nav_menu(
						array(
							'theme_location' => 'primary', // Oder ein spezifisches '404-menu'
							'menu_class'     => 'error-404-menu',
							'container'      => 'nav',
                            'container_class'=> 'error-404-menu-container',
							'depth'          => 1,
							'fallback_cb'    => false, // Kein Fallback, wenn Menü nicht existiert
						)
					);
				?>
				<p><a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php esc_html_e( 'Zurück zur Startseite', 'kneipp-petershagen-premium' ); ?></a></p>
			</div>

			<?php
			// Hier könnte die individuelle Grafik mit CTA zur Mitgliedschaft platziert werden.
			// Beispiel:
			// echo '<div class="cta-mitgliedschaft-404">';
			// echo '<img src="' . esc_url( KNEIPP_PREMIUM_THEME_URI . 'assets/images/404-mitglied-werden.png' ) . '" alt="' . esc_attr__( 'Werden Sie Mitglied im Kneippverein Petershagen', 'kneipp-petershagen-premium' ) . '">';
			// echo '<a href="/mitglied-werden/" class="button button-primary">' . esc_html__( 'Jetzt Mitglied werden!', 'kneipp-petershagen-premium' ) . '</a>';
			// echo '</div>';
			?>

		</div><!-- .page-content -->
	</section><!-- .error-404 -->

<?php
get_footer();
?>
