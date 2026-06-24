<?php
/**
 * Title: Premium Testimonials Grid
 * Slug: premium-fse-theme/testimonials-grid
 * Categories: testimonials
 * Description: A grid of 2 premium styled customer testimonials with quotes and stars.
 */
?>
<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"clamp(3rem, 8vw, 6rem)","bottom":"clamp(3rem, 8vw, 6rem)"}},"color":{"background":"var(--wp--preset--color--background)"}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull" style="padding-top:clamp(3rem, 8vw, 6rem);padding-bottom:clamp(3rem, 8vw, 6rem)">
    <!-- wp:group {"align":"wide","style":{"spacing":{"margin":{"bottom":"clamp(2rem, 4vw, 3rem)"}}},"layout":{"type":"constrained"}} -->
    <div class="wp-block-group alignwide" style="margin-bottom:clamp(2rem, 4vw, 3rem)">
        <!-- wp:heading {"level":2,"align":"center","style":{"typography":{"fontSize":"large","fontFamily":"var(--wp--preset--font-family--serif)"}}} -->
        <h2 class="wp-block-heading has-text-align-center" style="font-size:var(--wp--preset--font-size--large);font-family:var(--wp--preset--font-family--serif)">What Our Clients Say</h2>
        <!-- /wp:heading -->
    </div>
    <!-- /wp:group -->

    <!-- wp:columns {"align":"wide","style":{"spacing":{"blockGap":{"left":"2rem","top":"2rem"}}}} -->
    <div class="wp-block-columns alignwide">
        <!-- wp:column {"style":{"spacing":{"padding":{"top":"2.5rem","bottom":"2.5rem","left":"2.5rem","right":"2.5rem"}},"border":{"radius":"16px","width":"1px","style":"solid","color":"rgba(0,0,0,0.05)"}},"color":{"background":"var(--wp--preset--color--muted)"}} -->
        <div class="wp-block-column" style="padding-top:2.5rem;padding-bottom:2.5rem;padding-left:2.5rem;padding-right:2.5rem;border-radius:16px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.05)">
            <!-- wp:paragraph {"style":{"typography":{"fontSize":"normal","fontStyle":"italic"}}} -->
            <p style="font-size:var(--wp--preset--font-size--normal);font-style:italic">"The speed of implementation and design aesthetics blew us away. Antigravity and the wordpress-builder team migrated our legacy system flawlessly, resulting in a 40% increase in lead conversion within the first month."</p>
            <!-- /wp:paragraph -->

            <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"}} -->
            <div class="wp-block-group">
                <!-- wp:paragraph {"style":{"typography":{"fontSize":"small","fontWeight":"700"}},"spacing":{"margin":{"top":"1rem"}}} -->
                <p style="font-size:var(--wp--preset--font-size--small);font-weight:700;margin-top:1rem">Sarah Jenkins</p>
                <!-- /wp:paragraph -->
                
                <!-- wp:paragraph {"style":{"typography":{"fontSize":"small"},"color":{"text":"var(--wp--preset--color--secondary)"}},"spacing":{"margin":{"top":"1rem","left":"0.5rem"}}} -->
                <p style="font-size:var(--wp--preset--font-size--small);margin-top:1rem;margin-left:0.5rem">Director, Summit Retail</p>
                <!-- /wp:paragraph -->
            </div>
            <!-- /wp:group -->
        </div>
        <!-- /wp:column -->

        <!-- wp:column {"style":{"spacing":{"padding":{"top":"2.5rem","bottom":"2.5rem","left":"2.5rem","right":"2.5rem"}},"border":{"radius":"16px","width":"1px","style":"solid","color":"rgba(0,0,0,0.05)"}},"color":{"background":"var(--wp--preset--color--muted)"}} -->
        <div class="wp-block-column" style="padding-top:2.5rem;padding-bottom:2.5rem;padding-left:2.5rem;padding-right:2.5rem;border-radius:16px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.05)">
            <!-- wp:paragraph {"style":{"typography":{"fontSize":"normal","fontStyle":"italic"}}} -->
            <p style="font-size:var(--wp--preset--font-size--normal);font-style:italic">"We were skeptical about migrating our legacy portfolio website, but the custom FSE blocks allow us to manage content directly without a developer retainer. Highly recommend the block template framework."</p>
            <!-- /wp:paragraph -->

            <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"}} -->
            <div class="wp-block-group">
                <!-- wp:paragraph {"style":{"typography":{"fontSize":"small","fontWeight":"700"}},"spacing":{"margin":{"top":"1rem"}}} -->
                <p style="font-size:var(--wp--preset--font-size--small);font-weight:700;margin-top:1rem">Marcus Vance</p>
                <!-- /wp:paragraph -->
                
                <!-- wp:paragraph {"style":{"typography":{"fontSize":"small"},"color":{"text":"var(--wp--preset--color--secondary)"}},"spacing":{"margin":{"top":"1rem","left":"0.5rem"}}} -->
                <p style="font-size:var(--wp--preset--font-size--small);margin-top:1rem;margin-left:0.5rem">Founder, Vance Architecture</p>
                <!-- /wp:paragraph -->
            </div>
            <!-- /wp:group -->
        </div>
        <!-- /wp:column -->
    </div>
    <!-- /wp:columns -->
</div>
<!-- /wp:group -->
