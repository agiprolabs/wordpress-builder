<?php
/**
 * Title: Premium Split Hero
 * Slug: premium-fse-theme/hero-split
 * Categories: header, featured
 * Description: A professional split hero section with text, call to action buttons, and a showcase image.
 */
?>
<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"clamp(4rem, 10vw, 8rem)","bottom":"clamp(4rem, 10vw, 8rem)"}},"color":{"background":"var(--wp--preset--color--background)"}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull" style="padding-top:clamp(4rem, 10vw, 8rem);padding-bottom:clamp(4rem, 10vw, 8rem)">
    <!-- wp:columns {"align":"wide","style":{"spacing":{"blockGap":{"left":"clamp(2rem, 5vw, 4rem)","top":"clamp(2rem, 5vw, 4rem)"}}}} -->
    <div class="wp-block-columns alignwide">
        <!-- wp:column {"width":"55%","style":{"spacing":{"padding":{"right":"1.5rem"}}}} -->
        <div class="wp-block-column" style="flex-basis:55%;padding-right:1.5rem">
            <!-- wp:heading {"level":1,"style":{"typography":{"fontSize":"huge","lineHeight":"1.15","fontFamily":"var(--wp--preset--font-family--serif)"}}} -->
            <h1 class="wp-block-heading" style="font-size:var(--wp--preset--font-size--huge);font-family:var(--wp--preset--font-family--serif);line-height:1.15">Elevate Your Digital Brand Presence</h1>
            <!-- /wp:heading -->

            <!-- wp:paragraph {"style":{"typography":{"fontSize":"medium"},"spacing":{"margin":{"top":"1.5rem","bottom":"2rem"}}}} -->
            <p style="font-size:var(--wp--preset--font-size--medium);margin-top:1.5rem;margin-bottom:2rem">We create high-converting custom block experiences, custom plugin architectures, and full-funnel content migrations mapped directly to your business outcomes.</p>
            <!-- /wp:paragraph -->

            <!-- wp:buttons -->
            <div class="wp-block-buttons">
                <!-- wp:button {"className":"is-style-fill"} -->
                <div class="wp-block-button is-style-fill"><a class="wp-block-button__link wp-element-button" href="#contact">Book A Consultation</a></div>
                <!-- /wp:button -->
                
                <!-- wp:button {"className":"is-style-outline"} -->
                <div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button" href="#services">View Our Work</a></div>
                <!-- /wp:button -->
            </div>
            <!-- /wp:buttons -->
        </div>
        <!-- /wp:column -->

        <!-- wp:column {"width":"45%"} -->
        <div class="wp-block-column" style="flex-basis:45%">
            <!-- wp:image {"sizeSlug":"large","linkDestination":"none","style":{"border":{"radius":"12px"},"shadow":"0 12px 40px rgba(0, 0, 0, 0.12)"}} -->
            <figure class="wp-block-image size-large"><img src="/wp-content/themes/premium-fse-theme/assets/images/hero-default.jpg" alt="Showcase Visual" style="border-radius:12px"/></figure>
            <!-- /wp:image -->
        </div>
        <!-- /wp:column -->
    </div>
    <!-- /wp:columns -->
</div>
<!-- /wp:group -->
