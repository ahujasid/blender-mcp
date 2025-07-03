<?php
/**
 * Der Header für unser Theme.
 *
 * Diese Datei zeigt alles bis zum <main> Tag und beinhaltet den <head> sowie
 * den sichtbaren Header-Bereich (Logo, Navigation).
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package Kneippverein_Petershagen_Premium
 */
?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="profile" href="https://gmpg.org/xfn/11">

	<?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
	<a class="skip-link screen-reader-text" href="#content"><?php esc_html_e( 'Zum Inhalt springen', 'kneipp-petershagen-premium' ); ?></a>

	<header id="masthead" class="site-header" role="banner">
		<?php
		// Logik für dynamische Header-Bilder
		$header_image_url = '';
		$default_header_image_fallback = KNEIPP_PREMIUM_THEME_URI . 'assets/images/default-header.webp'; // Absoluter Fallback, falls Bild nicht existiert

		// Versuche, das Default-Header-Bild aus dem Customizer zu laden
		$default_header_image = get_theme_mod( 'default_header_bild', $default_header_image_fallback );
		if (empty($default_header_image)) { // Falls im Customizer gelöscht, nimm den harten Fallback
			$default_header_image = $default_header_image_fallback;
		}

		if ( is_front_page() ) {
			// Spezifisches Headerbild für die Startseite aus Theme Optionen
			$header_image_url = get_theme_mod( 'startseiten_header_bild', $default_header_image );
			if (empty($header_image_url)) { // Wenn Startseiten-Header leer, nimm Default
                $header_image_url = $default_header_image;
            }
		} elseif ( is_page() || (is_singular() && !is_attachment()) ) {
			// Versuche, ein seiten-spezifisches Header-Bild via Custom Field (ACF) zu laden
			// Annahme: ACF Feld 'seiten_header_bild' gibt eine Bild-ID oder URL zurück
			$custom_header_image_meta = get_post_meta( get_the_ID(), 'seiten_header_bild', true );
			if ( $custom_header_image_meta ) {
				if ( is_array( $custom_header_image_meta ) && isset( $custom_header_image_meta['url'] ) ) {
					$header_image_url = $custom_header_image_meta['url']; // ACF Bild-Array
				} elseif ( is_numeric( $custom_header_image_meta ) ) {
					$header_image_url = wp_get_attachment_image_url( $custom_header_image_meta, 'full' ); // ACF Bild-ID
				} elseif ( filter_var( $custom_header_image_meta, FILTER_VALIDATE_URL ) ) {
                    $header_image_url = $custom_header_image_meta; // Direkte URL
                }
			}
		} elseif ( is_tax( 'kneipp_pillar' ) || is_category() || is_tag() ) { // Für Taxonomie-Archive
			$term = get_queried_object();
			if ( $term && isset( $term->term_id ) ) {
				// Versuche, ein Header-Bild für den Taxonomie-Term zu laden (ACF Term-Meta)
				// Annahme: ACF Feld 'saeulen_header_bild' (oder generischer 'taxonomie_header_bild') gibt ID oder URL zurück
				$term_header_image_meta = get_term_meta( $term->term_id, 'saeulen_header_bild', true );
				if ( $term_header_image_meta ) {
					if ( is_array( $term_header_image_meta ) && isset( $term_header_image_meta['url'] ) ) {
						$header_image_url = $term_header_image_meta['url'];
					} elseif ( is_numeric( $term_header_image_meta ) ) {
						$header_image_url = wp_get_attachment_image_url( $term_header_image_meta, 'full' );
					} elseif ( filter_var( $term_header_image_meta, FILTER_VALIDATE_URL ) ) {
                        $header_image_url = $term_header_image_meta;
                    }
				}
			}
		}

		// Fallback auf das Default-Header-Bild, wenn keine spezifische URL gefunden wurde
		if ( empty( $header_image_url ) ) {
			$header_image_url = $default_header_image;
		}
		?>
        <div class="header-background-image" style="background-image: url('<?php echo esc_url( $header_image_url ); ?>');">
            <div class="header-overlay"> <?php // Für Text-Overlay über dem Bild, falls gewünscht ?>
                <div class="container"> <?php // Container für innere Elemente ?>
                    <div class="site-branding">
                        <?php
                        if ( has_custom_logo() ) {
                            the_custom_logo();
                        } elseif ( get_bloginfo( 'name' ) ) {
                            if ( is_front_page() && is_home() ) :
                                ?>
                                <h1 class="site-title"><a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home"><?php bloginfo( 'name' ); ?></a></h1>
                                <?php
                            else :
                                ?>
                                <p class="site-title"><a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home"><?php bloginfo( 'name' ); ?></a></p>
                                <?php
                            endif;
                            $kneipp_premium_description = get_bloginfo( 'description', 'display' );
                            if ( $kneipp_premium_description || is_customize_preview() ) :
                                ?>
                                <p class="site-description"><?php echo $kneipp_premium_description; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></p>
                            <?php endif; ?>
                        <?php } ?>
                    </div><!-- .site-branding -->

                    <nav id="site-navigation" class="main-navigation" role="navigation" aria-label="<?php esc_attr_e( 'Hauptmenü', 'kneipp-petershagen-premium' ); ?>">
                        <button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
                            <?php esc_html_e( 'Menü', 'kneipp-petershagen-premium' ); ?>
                            <?php // Optional: SVG Icon für Burger Menü ?>
                        </button>
                        <?php
                        wp_nav_menu(
                            array(
                                'theme_location' => 'primary', // Wird in inc/theme-setup.php registriert
                                'menu_id'        => 'primary-menu',
                                'menu_class'     => 'menu-primary', // Eigene Klasse für Styling
                                'container'      => false, // Keinen zusätzlichen div-Container um das Menü
                                'fallback_cb'    => 'kneipp_premium_primary_menu_fallback', // Fallback-Funktion
                                'items_wrap'     => '<ul id="%1$s" class="%2$s">%3$s</ul>',
                                // 'walker'         => new Kneipp_Premium_Mega_Menu_Walker(), // Wenn Mega-Menü-Walker aktiv ist
                            )
                        );
                        ?>
                    </nav><!-- #site-navigation -->
                </div><!-- .container -->
            </div><!-- .header-overlay -->
        </div><!-- .header-background-image -->
	</header><!-- #masthead -->

	<div id="content" class="site-content">
		<div class="container"> <?php // Ein Container für das Layout, kann angepasst werden ?>
			<main id="main" class="site-main" role="main">
