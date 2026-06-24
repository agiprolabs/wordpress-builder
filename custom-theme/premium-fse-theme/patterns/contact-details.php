<?php
/**
 * Title: Premium Contact Details
 * Slug: premium-fse-theme/contact-details
 * Categories: contact
 * Description: A split contact section with business details and a message placeholder.
 */
?>
<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"clamp(3rem, 8vw, 6rem)","bottom":"clamp(3rem, 8vw, 6rem)"}},"color":{"background":"var(--wp--preset--color--muted)"}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull" style="padding-top:clamp(3rem, 8vw, 6rem);padding-bottom:clamp(3rem, 8vw, 6rem)">
    <!-- wp:columns {"align":"wide","style":{"spacing":{"blockGap":{"left":"clamp(2rem, 5vw, 4rem)","top":"clamp(2rem, 5vw, 4rem)"}}}} -->
    <div class="wp-block-columns alignwide">
        <!-- wp:column {"width":"45%"} -->
        <div class="wp-block-column" style="flex-basis:45%">
            <!-- wp:heading {"level":2,"style":{"typography":{"fontSize":"large","fontFamily":"var(--wp--preset--font-family--serif)"}}} -->
            <h2 class="wp-block-heading" style="font-size:var(--wp--preset--font-size--large);font-family:var(--wp--preset--font-family--serif)">Get In Touch</h2>
            <!-- /wp:heading -->

            <!-- wp:paragraph {"style":{"spacing":{"margin":{"top":"1rem","bottom":"2rem"}}}} -->
            <p style="margin-top:1rem;margin-bottom:2rem">Have questions or want to discuss a project? Reach out to us directly through any of our channels or send a message using the form.</p>
            <!-- /wp:paragraph -->

            <!-- wp:group {"style":{"spacing":{"blockGap":"1.5rem"}},"layout":{"type":"constrained"}} -->
            <div class="wp-block-group">
                <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"}} -->
                <div class="wp-block-group">
                    <!-- wp:paragraph {"style":{"typography":{"fontWeight":"700"}}} -->
                    <p style="font-weight:700">Phone:</p>
                    <!-- /wp:paragraph -->
                    <!-- wp:paragraph {"style":{"spacing":{"margin":{"left":"0.5rem"}}}} -->
                    <p style="margin-left:0.5rem"><a href="tel:{{BUSINESS_PHONE}}">{{BUSINESS_PHONE}}</a></p>
                    <!-- /wp:paragraph -->
                </div>
                <!-- /wp:group -->

                <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"}} -->
                <div class="wp-block-group">
                    <!-- wp:paragraph {"style":{"typography":{"fontWeight":"700"}}} -->
                    <p style="font-weight:700">Email:</p>
                    <!-- /wp:paragraph -->
                    <!-- wp:paragraph {"style":{"spacing":{"margin":{"left":"0.5rem"}}}} -->
                    <p style="margin-left:0.5rem"><a href="mailto:{{BUSINESS_EMAIL}}">{{BUSINESS_EMAIL}}</a></p>
                    <!-- /wp:paragraph -->
                </div>
                <!-- /wp:group -->

                <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"}} -->
                <div class="wp-block-group">
                    <!-- wp:paragraph {"style":{"typography":{"fontWeight":"700"}}} -->
                    <p style="font-weight:700">Address:</p>
                    <!-- /wp:paragraph -->
                    <!-- wp:paragraph {"style":{"spacing":{"margin":{"left":"0.5rem"}}}} -->
                    <p style="margin-left:0.5rem">{{BUSINESS_ADDRESS}}</p>
                    <!-- /wp:paragraph -->
                </div>
                <!-- /wp:group -->
            </div>
            <!-- /wp:group -->
        </div>
        <!-- /wp:column -->

        <!-- wp:column {"width":"55%","style":{"spacing":{"padding":{"top":"2rem","bottom":"2rem","left":"2rem","right":"2rem"}},"border":{"radius":"12px"}},"color":{"background":"var(--wp--preset--color--background)"}} -->
        <div class="wp-block-column" style="flex-basis:55%;padding-top:2rem;padding-bottom:2rem;padding-left:2rem;padding-right:2rem;border-radius:12px">
            <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium"}}} -->
            <h3 class="wp-block-heading" style="font-size:var(--wp--preset--font-size--medium)">Send a Message</h3>
            <!-- /wp:heading -->

            <!-- wp:paragraph {"style":{"spacing":{"margin":{"top":"1rem"}}}} -->
            <p style="margin-top:1rem">Please contact us using the phone or email directly, or drop by during office hours.</p>
            <!-- /wp:paragraph -->
        </div>
        <!-- /wp:column -->
    </div>
    <!-- /wp:columns -->
</div>
<!-- /wp:group -->
