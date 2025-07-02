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
				)
			);
			?>
		</nav><!-- #site-navigation -->
	</header><!-- #masthead -->

	<div id="content" class="site-content">
		<div class="container"> <?php // Ein Container für das Layout, kann angepasst werden ?>
			<main id="main" class="site-main" role="main">
