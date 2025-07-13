<?php
/**
 * Template Part für die Anzeige, wenn keine Beiträge gefunden wurden.
 * (z.B. in Archiven ohne Beiträge oder bei einer leeren Suche).
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/
 *
 * @package Kneippverein_Petershagen_Premium
 */
?>

<section class="no-results not-found">
	<header class="page-header">
		<h1 class="page-title"><?php esc_html_e( 'Nichts gefunden', 'kneipp-petershagen-premium' ); ?></h1>
	</header><!-- .page-header -->

	<div class="page-content">
		<?php
		if ( is_home() && current_user_can( 'publish_posts' ) ) : // Wenn auf der Blog-Startseite und der Nutzer Beiträge erstellen kann

			printf(
				'<p>' . wp_kses(
					/* translators: 1: link to WP admin new post page. */
					__( 'Bereit, deinen ersten Beitrag zu veröffentlichen? <a href="%1$s">Starte hier</a>.', 'kneipp-petershagen-premium' ),
					array(
						'a' => array(
							'href' => array(),
						),
					)
				) . '</p>',
				esc_url( admin_url( 'post-new.php' ) )
			);

		elseif ( is_search() ) : // Wenn auf einer Suchergebnisseite

			?>
			<p><?php esc_html_e( 'Entschuldigung, aber für Ihre Suchanfrage wurden keine Ergebnisse gefunden. Bitte versuchen Sie es mit anderen Suchbegriffen.', 'kneipp-petershagen-premium' ); ?></p>
			<?php
			get_search_form();

		else : // Für alle anderen Fälle (Archive etc.)

			?>
			<p><?php esc_html_e( 'Es scheint, wir können nicht finden, wonach Sie suchen. Vielleicht hilft eine Suche?', 'kneipp-petershagen-premium' ); ?></p>
			<?php
			get_search_form();

		endif;
		?>
	</div><!-- .page-content -->
</section><!-- .no-results -->
