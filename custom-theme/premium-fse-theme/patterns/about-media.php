<?php
/**
 * Title: Premium About Details
 * Slug: premium-fse-theme/about-media
 * Categories: about
 * Description: An editorial About Us section with side-by-side text and media.
 */
?>
<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"clamp(3rem, 8vw, 6rem)","bottom":"clamp(3rem, 8vw, 6rem)"}},"color":{"background":"var(--wp--preset--color--background)"}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull" style="padding-top:clamp(3rem, 8vw, 6rem);padding-bottom:clamp(3rem, 8vw, 6rem)">
    <!-- wp:columns {"align":"wide","style":{"spacing":{"blockGap":{"left":"clamp(2rem, 5vw, 4rem)","top":"clamp(2rem, 5vw, 4rem)"}}}} -->
    <div class="wp-block-columns alignwide">
        <!-- wp:column {"width":"45%"} -->
        <div class="wp-block-column" style="flex-basis:45%">
            <!-- wp:image {"sizeSlug":"large","linkDestination":"none","style":{"border":{"radius":"12px"}}} -->
            <figure class="wp-block-image size-large"><img src="/wp-content/themes/premium-fse-theme/assets/images/about-default.jpg" alt="Our Team / Studio" style="border-radius:12px"/></figure>
            <!-- /wp:image -->
        </div>
        <!-- /wp:column -->

        <!-- wp:column {"width":"55%","style":{"spacing":{"padding":{"left":"1.5rem"}}}} -->
        <div class="wp-block-column" style="flex-basis:55%;padding-left:1.5rem">
            <!-- wp:heading {"level":2,"style":{"typography":{"fontSize":"large","fontFamily":"var(--wp--preset--font-family--serif)"}}} -->
            <h2 class="wp-block-heading" style="font-size:var(--wp--preset--font-size--large);font-family:var(--wp--preset--font-family--serif)">Our Philosophy</h2>
            <!-- /wp:heading -->

            <!-- wp:paragraph {"style":{"typography":{"fontSize":"normal"},"spacing":{"margin":{"top":"1.5rem","bottom":"1.5rem"}}}} -->
            <p style="font-size:var(--wp--preset--font-size--normal);margin-top:1.5rem;margin-bottom:1.5rem">We believe that a professional digital presence is the core driver of modern business scaling. By pairing clean design principles with robust full site editing capabilities, we give our clients absolute control over their brand story.</p>
            <!-- /wp:paragraph -->

            <!-- wp:paragraph {"style":{"typography":{"fontSize":"normal"}}} -->
            <p style="font-size:var(--wp--preset--font-size--normal)">Every website we migrate or build from scratch is checked against rigorous accessibility guidelines, viewport scaling matrices, and SEO compliance systems. The result is a fast, beautiful site that ranks well and converts visitors into loyal clients.</p>
            <!-- /wp:paragraph -->
        </div>
        <!-- /wp:column -->
    </div>
    <!-- /wp:columns -->
</div>
<!-- /wp:group -->
