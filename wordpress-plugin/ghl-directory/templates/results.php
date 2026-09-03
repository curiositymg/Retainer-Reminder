<?php
/**
 * Contact grid.
 *
 * Override by copying this file to your-theme/ghl-directory/results.php.
 *
 * @package GHL_Directory
 * @var array $data items, scope, total.
 */

defined( 'ABSPATH' ) || exit;

if ( empty( $data['items'] ) ) {
	printf( '<p class="ghld-empty">%s</p>', esc_html( $data['scope']['empty'] ) );

	return;
}
?>
<ul class="ghld-grid" role="list">
	<?php foreach ( $data['items'] as $ghld_contact ) : ?>
		<li class="ghld-grid-item">
			<?php
			GHLD_Template::render(
				'contact-card',
				array(
					'contact' => $ghld_contact,
					'scope'   => $data['scope'],
				)
			);
			?>
		</li>
	<?php endforeach; ?>
</ul>
