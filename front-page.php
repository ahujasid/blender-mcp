<?php
/**
 * Das Template für die Anzeige der Startseite.
 *
 * Dies ist das Template, das für die als "Startseite" festgelegte Seite verwendet wird.
 * Es überschreibt home.php und index.php für die Startseiten-Anzeige.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/#front-page-display
 *
 * @package Kneippverein_Petershagen_Premium
 */

get_header();
?>

	<?php
	// Startseiten-spezifischer Inhalt, der über den Editor der als Startseite festgelegten Seite gepflegt wird.
	if ( have_posts() ) :
		while ( have_posts() ) :
			the_post();
			?>
			<article id="post-<?php the_ID(); ?>" <?php post_class('front-page-content-area'); ?>>
				<div class="entry-content">
					<?php the_content(); ?>
				</div><!-- .entry-content -->
			</article><!-- #post-<?php the_ID(); ?> -->
			<?php
		endwhile;
	else :
		// Fallback, falls der Startseite kein Inhalt zugewiesen wurde oder die Seite nicht existiert.
		?>
		<section class="no-content-found">
			<p><?php esc_html_e( 'Bitte weisen Sie eine Seite als Startseite zu und fügen Sie Inhalte hinzu.', 'kneipp-petershagen-premium' ); ?></p>
		</section>
		<?php
	endif;
	?>

	<?php
	// Beispielhafte Sektion für die "5 Säulen" Teaser
	// Diese Sektion könnte später durch einen individuellen Gutenberg-Block ("Kneipp-Säulen Teaser")
	// oder durch manuell hinzugefügte Blöcke im Editor der Startseite realisiert werden.
	// Für den Moment ist dies ein Platzhalter, der zeigt, wo solche Inhalte platziert werden könnten.
	?>
	<section id="five-pillars-teaser" class="front-page-section five-pillars-section">
		<div class="container">
			<h2 class="section-title"><?php esc_html_e( 'Die 5 Säulen der Kneipp-Lehre', 'kneipp-petershagen-premium' ); ?></h2>
			<div class="pillars-grid">
				<?php
				$pillars = array(
					'wasser' => array(
						'title' => __( 'Wasser', 'kneipp-petershagen-premium' ),
						'icon'  => 'water', // Annahme: SVG-Icon-Name oder CSS-Klasse
						'link'  => home_url( '/wasser/' ), // Annahme: Seite /wasser/ existiert
						'text'  => __( 'Die Kraft des Wassers entdecken und für Gesundheit und Wohlbefinden nutzen.', 'kneipp-petershagen-premium' ),
					),
					'pflanzen' => array(
						'title' => __( 'Heilpflanzen', 'kneipp-petershagen-premium' ),
						'icon'  => 'leaf',
						'link'  => home_url( '/heilpflanzen/' ),
						'text'  => __( 'Die Natur als Apotheke: Lernen Sie die Wirkung heimischer Kräuter kennen.', 'kneipp-petershagen-premium' ),
					),
					'bewegung' => array(
						'title' => __( 'Bewegung', 'kneipp-petershagen-premium' ),
						'icon'  => 'directions_walk', // Material Icon Beispiel
						'link'  => home_url( '/bewegung/' ),
						'text'  => __( 'Aktive Lebensgestaltung durch maßvolle Bewegung in der Natur und im Alltag.', 'kneipp-petershagen-premium' ),
					),
					'ernaehrung' => array(
						'title' => __( 'Ernährung', 'kneipp-petershagen-premium' ),
						'icon'  => 'restaurant',
						'link'  => home_url( '/ernaehrung/' ),
						'text'  => __( 'Vollwertige und naturbelassene Kost als Basis für ein gesundes Leben.', 'kneipp-petershagen-premium' ),
					),
					'balance' => array(
						'title' => __( 'Lebensordnung', 'kneipp-petershagen-premium' ),
						'icon'  => 'spa',
						'link'  => home_url( '/lebensordnung/' ), // Du hattest "Lebnsordnug" - korrigiert zu "lebensordnung"
						'text'  => __( 'Innere Harmonie und seelisches Gleichgewicht für ein erfülltes Dasein.', 'kneipp-petershagen-premium' ),
					),
				);

				foreach ( $pillars as $slug => $pillar ) :
				?>
					<div class="pillar-item pillar-<?php echo esc_attr( $slug ); ?>">
						<div class="pillar-icon">
							<?php // Hier könnte kneipp_premium_get_icon($pillar['icon']) aufgerufen werden, wenn Icons bereitstehen ?>
                            <span class="icon-placeholder"><?php echo esc_html( strtoupper( substr( $pillar['title'], 0, 1 ) ) ); ?></span>
						</div>
						<h3 class="pillar-title"><a href="<?php echo esc_url( $pillar['link'] ); ?>"><?php echo esc_html( $pillar['title'] ); ?></a></h3>
						<p class="pillar-text"><?php echo esc_html( $pillar['text'] ); ?></p>
						<a href="<?php echo esc_url( $pillar['link'] ); ?>" class="pillar-learn-more button button-secondary"><?php esc_html_e( 'Mehr erfahren', 'kneipp-petershagen-premium' ); ?></a>
					</div>
				<?php
				endforeach;
				?>
			</div><!-- .pillars-grid -->
		</div><!-- .container -->
	</section><!-- #five-pillars-teaser -->

	<?php
	// Weitere Sektionen für die Startseite könnten hier folgen, z.B.:
	// - Aktuelle Kurse / Veranstaltungen (Loop mit CPTs)
	// - News / Blog-Vorschau
	// - Testimonials
	// - Call to Action zur Mitgliedschaft
	?>
    <section id="upcoming-events-teaser" class="front-page-section upcoming-events-section">
        <div class="container">
            <h2 class="section-title"><?php esc_html_e( 'Aktuelle Veranstaltungen', 'kneipp-petershagen-premium' ); ?></h2>
            <?php
            $upcoming_events_query = new WP_Query( array(
                'post_type' => 'event', // Unser CPT "Veranstaltung"
                'posts_per_page' => 3,
                'meta_key' => 'veranstaltung_datum_start', // Annahme: ACF Feld für Startdatum
                'orderby' => 'meta_value',
                'order' => 'ASC',
                'meta_query' => array(
                    array(
                        'key' => 'veranstaltung_datum_start',
                        'value' => date('Y-m-d'), // Heutiges Datum
                        'compare' => '>=',
                        'type' => 'DATE'
                    )
                )
            ) );

            if ( $upcoming_events_query->have_posts() ) :
                echo '<div class="events-grid">';
                while ( $upcoming_events_query->have_posts() ) : $upcoming_events_query->the_post();
                    // Hier könnte ein Template Part für Veranstaltungs-Teaser geladen werden
                    // get_template_part('parts/content', 'excerpt-event');
                    ?>
                    <article id="event-<?php the_ID(); ?>" <?php post_class('event-teaser-item'); ?>>
                        <?php if ( has_post_thumbnail() ) : ?>
                            <div class="event-thumbnail">
                                <a href="<?php the_permalink(); ?>"><?php the_post_thumbnail('medium'); ?></a>
                            </div>
                        <?php endif; ?>
                        <h3 class="event-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
                        <div class="event-meta">
                            <?php
                            // $event_date = get_post_meta(get_the_ID(), 'veranstaltung_datum_start', true);
                            // if ($event_date) {
                            //    echo '<span class="event-date">' . esc_html(date_i18n(get_option('date_format'), strtotime($event_date))) . '</span>';
                            // }
                            ?>
                        </div>
                        <a href="<?php the_permalink(); ?>" class="button button-secondary"><?php esc_html_e('Details', 'kneipp-petershagen-premium'); ?></a>
                    </article>
                    <?php
                endwhile;
                echo '</div>';
                wp_reset_postdata();
            else :
                echo '<p>' . esc_html__( 'Zurzeit sind keine bevorstehenden Veranstaltungen geplant.', 'kneipp-petershagen-premium' ) . '</p>';
            endif;
            ?>
            <p class="all-events-link"><a href="<?php echo esc_url( get_post_type_archive_link('event') ); ?>" class="button"><?php esc_html_e( 'Alle Veranstaltungen anzeigen', 'kneipp-petershagen-premium' ); ?></a></p>
        </div>
    </section>

<?php
get_footer();
?>
