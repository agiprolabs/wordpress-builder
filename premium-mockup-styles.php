<?php
/**
 * Plugin Name: Premium Mockup Styles
 * Description: Injects Google Fonts, custom CSS variables, modern Gutenberg layout polishing, and a dynamic contact header bar.
 * Version: 1.1
 * Author: gilbert.studio
 */

add_action('wp_head', function() {
    ?>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Modern Design System Overrides */
        :root {
            --wp--preset--font-family--sans-serif: var(--body-font, 'Inter', sans-serif) !important;
            --wp--preset--font-family--serif: var(--heading-font, 'Playfair Display', serif) !important;
            --wp--preset--font-family--heading: var(--heading-font, 'Outfit', sans-serif) !important;
            --wp--preset--font-family--body: var(--body-font, 'Inter', sans-serif) !important;
            
            /* Theme overrides for default font types */
            --wp--preset--font-family--albert-sans: var(--body-font, 'Inter', sans-serif) !important;
            --wp--preset--font-family--dmsans: var(--body-font, 'Inter', sans-serif) !important;
            --wp--preset--font-family--playfair-display: var(--heading-font, 'Playfair Display', serif) !important;
        }

        body {
            font-family: var(--body-font, 'Inter', -apple-system, sans-serif) !important;
            color: var(--wp--preset--color--contrast, #334155) !important;
            background-color: var(--wp--preset--color--base, #fdfdfd) !important;
            -webkit-font-smoothing: antialiased;
            margin: 0 !important;
        }

        /* Set clean headings with Outfit/Serif font */
        h1, h2, h3, h4, h5, h6, 
        .wp-block-site-title,
        .wp-block-site-title a,
        .wp-block-heading,
        .wp-block-post-title {
            font-family: var(--heading-font, 'Outfit', sans-serif) !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            color: var(--wp--preset--color--contrast, #0f172a) !important;
            line-height: 1.25 !important;
        }

        /* Hide redundant post title (e.g. "Home") */
        .home .wp-block-post-title,
        .wp-block-post-title {
            display: none !important;
        }

        /* 1. Local Home Services */
        body.vertical-home_services {
            --primary-bg: #f8fafc !important;
            --primary-text: #1e293b !important;
            --accent-color: #ea580c !important;
            --accent-hover: #c2410c !important;
            --heading-font: 'Outfit', sans-serif !important;
            --body-font: 'Inter', sans-serif !important;
            background-color: #ffffff !important;

            /* Override WordPress Theme Presets */
            --wp--preset--color--base: #ffffff !important;
            --wp--preset--color--contrast: #1e293b !important;
            --wp--preset--color--accent-1: #ea580c !important;
            --wp--preset--color--accent-2: #f8fafc !important;
            --wp--preset--color--accent-3: #cbd5e1 !important;
            --wp--preset--color--accent-4: #64748b !important;
            --wp--preset--color--accent-5: #0f172a !important;
            --wp--preset--color--accent-6: rgba(234, 88, 12, 0.1) !important;
        }
        
        /* 2. Health, Wellness & Beauty */
        body.vertical-health_wellness {
            --primary-bg: #f5f5f4 !important;
            --primary-text: #78716c !important;
            --accent-color: #d97706 !important;
            --accent-hover: #b45309 !important;
            --heading-font: 'Playfair Display', Georgia, serif !important;
            --body-font: 'Inter', sans-serif !important;
            background-color: #fdfdfd !important;

            /* Override WordPress Theme Presets */
            --wp--preset--color--base: #fdfdfd !important;
            --wp--preset--color--contrast: #78716c !important;
            --wp--preset--color--accent-1: #d97706 !important;
            --wp--preset--color--accent-2: #f5f5f4 !important;
            --wp--preset--color--accent-3: #e7e5e4 !important;
            --wp--preset--color--accent-4: #a8a29e !important;
            --wp--preset--color--accent-5: #44403c !important;
            --wp--preset--color--accent-6: rgba(217, 119, 6, 0.1) !important;
        }

        /* 3. Medical & Professional */
        body.vertical-medical_professional {
            --primary-bg: #f1f5f9 !important;
            --primary-text: #0f172a !important;
            --accent-color: #0d9488 !important;
            --accent-hover: #0f766e !important;
            --heading-font: 'Inter', sans-serif !important;
            --body-font: 'Inter', sans-serif !important;
            background-color: #ffffff !important;

            /* Override WordPress Theme Presets */
            --wp--preset--color--base: #ffffff !important;
            --wp--preset--color--contrast: #0f172a !important;
            --wp--preset--color--accent-1: #0d9488 !important;
            --wp--preset--color--accent-2: #f1f5f9 !important;
            --wp--preset--color--accent-3: #cbd5e1 !important;
            --wp--preset--color--accent-4: #475569 !important;
            --wp--preset--color--accent-5: #1e293b !important;
            --wp--preset--color--accent-6: rgba(13, 148, 136, 0.1) !important;
        }

        /* 4. Modern Tech & SaaS */
        body.vertical-tech_saas {
            --primary-bg: #18181b !important;
            --primary-text: #f4f4f5 !important;
            --accent-color: #a855f7 !important;
            --accent-hover: #9333ea !important;
            --heading-font: 'Outfit', sans-serif !important;
            --body-font: 'Inter', sans-serif !important;
            background-color: #09090b !important;
            color: #e4e4e7 !important;

            /* Override WordPress Theme Presets */
            --wp--preset--color--base: #09090b !important;
            --wp--preset--color--contrast: #f4f4f5 !important;
            --wp--preset--color--accent-1: #a855f7 !important;
            --wp--preset--color--accent-2: #18181b !important;
            --wp--preset--color--accent-3: #27272a !important;
            --wp--preset--color--accent-4: #71717a !important;
            --wp--preset--color--accent-5: #09090b !important;
            --wp--preset--color--accent-6: rgba(168, 85, 247, 0.15) !important;
        }
        body.vertical-tech_saas p, 
        body.vertical-tech_saas li, 
        body.vertical-tech_saas a:not(.top-bar-btn):not(.wp-block-button__link) {
            color: #a1a1aa !important;
        }

        /* 5. Restaurant & Food */
        body.vertical-restaurant_food {
            --primary-bg: #fffbeb !important;
            --primary-text: #18181b !important;
            --accent-color: #c2410c !important;
            --accent-hover: #9a3412 !important;
            --heading-font: 'Playfair Display', Georgia, serif !important;
            --body-font: 'Inter', sans-serif !important;
            background-color: #fffdf5 !important;

            /* Override WordPress Theme Presets */
            --wp--preset--color--base: #fffdf5 !important;
            --wp--preset--color--contrast: #18181b !important;
            --wp--preset--color--accent-1: #c2410c !important;
            --wp--preset--color--accent-2: #fffbeb !important;
            --wp--preset--color--accent-3: #e4e4e7 !important;
            --wp--preset--color--accent-4: #52525b !important;
            --wp--preset--color--accent-5: #27272a !important;
            --wp--preset--color--accent-6: rgba(194, 65, 12, 0.1) !important;
        }

        /* 6. Professional & Legal */
        body.vertical-professional_services {
            --primary-bg: #fafaf9 !important;
            --primary-text: #1e3a8a !important;
            --accent-color: #b45309 !important;
            --accent-hover: #78350f !important;
            --heading-font: 'Playfair Display', Georgia, serif !important;
            --body-font: 'Inter', sans-serif !important;
            background-color: #ffffff !important;

            /* Override WordPress Theme Presets */
            --wp--preset--color--base: #ffffff !important;
            --wp--preset--color--contrast: #111827 !important;
            --wp--preset--color--accent-1: #b45309 !important;
            --wp--preset--color--accent-2: #fafaf9 !important;
            --wp--preset--color--accent-3: #e5e7eb !important;
            --wp--preset--color--accent-4: #4b5563 !important;
            --wp--preset--color--accent-5: #1e3a8a !important;
            --wp--preset--color--accent-6: rgba(180, 83, 9, 0.1) !important;
        }

        /* 7. Armand Gilbert 1:1 Replica */
        @font-face {
            font-family: 'ColaborateThinRegular';
            src: url('/wp-content/themes/premium-fse-theme/fonts/ColabThi-webfont.eot');
            src: url('/wp-content/themes/premium-fse-theme/fonts/ColabThi-webfont.eot?#iefix') format('embedded-opentype'),
                 url('/wp-content/themes/premium-fse-theme/fonts/ColabThi-webfont.woff') format('woff'),
                 url('/wp-content/themes/premium-fse-theme/fonts/ColabThi-webfont.ttf') format('truetype'),
                 url('/wp-content/themes/premium-fse-theme/fonts/ColabThi-webfont.svg#ColaborateThinRegular') format('svg');
            font-weight: normal;
            font-style: normal;
        }

        body.vertical-armand_gilbert {
            background: #575757 url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/bg.jpg") repeat !important;
            color: #333333 !important;
            font-family: Arial, Helvetica, sans-serif !important;
            font-size: 13px !important;
            line-height: 20px !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        body.vertical-armand_gilbert p,
        body.vertical-armand_gilbert li,
        body.vertical-armand_gilbert blockquote {
            color: #333333 !important;
            font-family: Arial, Helvetica, sans-serif !important;
            font-size: 13px !important;
            line-height: 20px !important;
        }

        body.vertical-armand_gilbert a {
            color: #986c04 !important;
            text-decoration: none !important;
        }
        body.vertical-armand_gilbert a:hover {
            text-decoration: underline !important;
        }

        body.vertical-armand_gilbert h1,
        body.vertical-armand_gilbert h2,
        body.vertical-armand_gilbert h3,
        body.vertical-armand_gilbert h4,
        body.vertical-armand_gilbert h5,
        body.vertical-armand_gilbert h6 {
            color: #332b24 !important;
            font-family: 'ColaborateThinRegular', Arial, sans-serif !important;
            font-weight: normal !important;
            letter-spacing: normal !important;
        }

        body.vertical-armand_gilbert strong {
            color: #1c1c1c !important;
        }

        /* Header / Top */
        body.vertical-armand_gilbert #top {
            background: #d2d2d2 url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/top-bg.png") repeat-x !important;
            border-bottom: 1px solid #ffffff !important;
            padding-top: 0px !important;
            height: 165px !important;
            width: 100% !important;
            position: relative !important;
            margin: 0 !important;
            z-index: 100 !important;
        }
        body.vertical-armand_gilbert #top .container {
            width: 960px !important;
            height: 165px !important;
            margin: 0 auto !important;
            position: relative !important;
        }
        body.vertical-armand_gilbert #header {
            width: 960px !important;
            height: 165px !important;
            margin: 0 auto !important;
            position: relative !important;
        }
        body.vertical-armand_gilbert #logo {
            position: absolute !important;
            top: 0px !important;
            left: 0px !important;
            width: 947px !important;
            height: 480px !important;
            max-width: none !important;
            max-height: none !important;
            z-index: 10 !important;
            border: none !important;
            box-shadow: none !important;
        }
        body.vertical-armand_gilbert #menu {
            position: absolute !important;
            top: 111px !important;
            left: 0px !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/menu-bg.png") no-repeat !important;
            width: 960px !important;
            height: 55px !important;
            z-index: 20 !important;
        }
        body.vertical-armand_gilbert #menu .wp-block-navigation {
            height: 100% !important;
        }
        body.vertical-armand_gilbert #menu ul.wp-block-navigation__container {
            margin: 0 !important;
            padding: 0 20px 0 0 !important;
            list-style: none !important;
            display: flex !important;
            justify-content: flex-end !important;
            align-items: center !important;
            height: 100% !important;
        }
        body.vertical-armand_gilbert #menu ul.wp-block-navigation__container > li {
            margin: 0 !important;
            padding: 0 !important;
        }
        body.vertical-armand_gilbert #menu ul.wp-block-navigation__container > li > a {
            font-family: 'ColaborateThinRegular', Arial, sans-serif !important;
            font-size: 15px !important;
            font-weight: bold !important;
            color: #ffffff !important;
            text-shadow: 1px 1px 1px #000000 !important;
            padding: 0 15px !important;
            line-height: 55px !important;
            display: block !important;
            height: 55px !important;
            text-decoration: none !important;
        }
        body.vertical-armand_gilbert #menu ul.wp-block-navigation__container > li > a:hover {
            color: #986c04 !important;
            text-decoration: none !important;
        }
        body.vertical-armand_gilbert #menu ul.wp-block-navigation__container > li.current-menu-item > a,
        body.vertical-armand_gilbert #menu ul.wp-block-navigation__container > li.current_page_item > a {
            color: #986c04 !important;
        }

        /* Content Full wrapper */
        body.vertical-armand_gilbert #content-full {
            width: 1280px !important;
            margin: 0 auto !important;
            background-color: #ffffff !important;
            position: relative !important;
            z-index: 5 !important;
            box-shadow: 0px 0px 20px rgba(0,0,0,0.15) !important;
            padding: 0 !important;
        }
        body.vertical-armand_gilbert #home-top {
            width: 100% !important;
            height: 102px !important;
            background: #d2d2d2 url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/top-bg.png") repeat-x !important;
            position: absolute !important;
            top: -1px !important;
            left: 0px !important;
            z-index: 1 !important;
        }
        body.vertical-armand_gilbert .wp-block-post-content.is-layout-constrained > :where(:not(.alignleft):not(.alignright):not(.alignfull)) {
            max-width: none !important;
            margin-left: unset !important;
            margin-right: unset !important;
        }
        body.vertical-armand_gilbert.home #hr {
            height: 628px !important;
        }
        body.vertical-armand_gilbert #hr {
            width: 100% !important;
            height: 75px !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/shadow-bar-bg.png") repeat-x !important;
            position: relative !important;
            z-index: 2 !important;
        }
        body.vertical-armand_gilbert.home #hr-center {
            height: 628px !important;
        }
        body.vertical-armand_gilbert #hr-center {
            width: 100% !important;
            height: 75px !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/shadow-bar-centerbg.png") no-repeat bottom center !important;
            position: relative !important;
        }
        body.vertical-armand_gilbert.home #intro {
            width: 100% !important;
            height: 628px !important;
            background: url("https://www.armandgilbert.com/wp-content/uploads/2016/11/brown-background.jpg") repeat !important;
            position: relative !important;
        }
        body.vertical-armand_gilbert .center-highlight {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/light-overlay.png") repeat-x !important;
            width: 100% !important;
            height: 100% !important;
        }
        body.vertical-armand_gilbert.home #intro .center-highlight {
            height: 628px !important;
        }

        /* Slider Featured */
        body.vertical-armand_gilbert #featured {
            position: relative !important;
            padding-bottom: 31px !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-bottom-shadow.png") no-repeat bottom left !important;
            height: 447px !important;
            width: 960px !important;
            margin: 0 auto !important;
            z-index: 4 !important;
            top: 40px !important;
        }
        body.vertical-armand_gilbert #featured span#left-shadow {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-leftshadow.png") no-repeat !important;
            width: 9px !important;
            height: 132px !important;
            display: block !important;
            position: absolute !important;
            z-index: 10 !important;
            top: -30px !important;
            left: -9px !important;
        }
        body.vertical-armand_gilbert #featured span#right-shadow {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-rightshadow.png") no-repeat !important;
            width: 9px !important;
            height: 132px !important;
            display: block !important;
            position: absolute !important;
            z-index: 10 !important;
            top: -30px !important;
            right: -9px !important;
        }
        body.vertical-armand_gilbert #slides {
            position: relative !important;
            width: 960px !important;
            height: 447px !important;
            overflow: hidden !important;
        }
        body.vertical-armand_gilbert .slide {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            opacity: 0 !important;
            transition: opacity 0.8s ease-in-out !important;
            z-index: 1 !important;
        }
        body.vertical-armand_gilbert .slide.active {
            opacity: 1 !important;
            z-index: 2 !important;
        }
        body.vertical-armand_gilbert .portfolio-slide-img {
            width: 960px !important;
            height: 447px !important;
            object-fit: cover !important;
        }
        body.vertical-armand_gilbert .slide .overlay,
        body.vertical-armand_gilbert .slide .overlay2 {
            display: none !important;
        }
        body.vertical-armand_gilbert #slides .description {
            line-height: 18px !important;
            color: #666666 !important;
            text-shadow: 1px 1px 1px #ffffff !important;
            font-size: 12px !important;
            position: absolute !important;
            top: 33px !important;
            right: 0px !important;
            width: 275px !important;
            z-index: 14 !important;
            box-sizing: border-box !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/description-top.png") no-repeat top center !important;
            padding-top: 19px !important;
            text-align: left !important;
        }
        body.vertical-armand_gilbert #slides .description .outer-content {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/description-center-outer.png") repeat-y !important;
            padding: 0px 1px 0px 7px !important;
        }
        body.vertical-armand_gilbert #slides .description .inner-content {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/description-center-inner.png") repeat-x bottom left !important;
            padding: 3px 16px 10px 28px !important;
        }
        body.vertical-armand_gilbert #slides .description .bottom {
            height: 36px !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/description-bottom.png") no-repeat !important;
        }
        body.vertical-armand_gilbert #slides .description h2.title {
            font-size: 26px !important;
            padding-bottom: 5px !important;
            margin: 0 !important;
            font-weight: normal !important;
            font-family: 'ColaborateThinRegular', Arial, sans-serif !important;
        }
        body.vertical-armand_gilbert #slides .description h2.title a {
            color: #363636 !important;
            text-decoration: none !important;
        }
        body.vertical-armand_gilbert #slides .description h2.title a:hover {
            color: #986c04 !important;
        }
        body.vertical-armand_gilbert #slides .description p {
            font-size: 12px !important;
            line-height: 18px !important;
            color: #666666 !important;
            margin: 0 0 10px 0 !important;
        }
        body.vertical-armand_gilbert #slides .description a.readmore {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-readmore.png") no-repeat bottom right !important;
            font-size: 12px !important;
            color: #ffffff !important;
            text-shadow: -1px -1px 1px #000000 !important;
            padding-right: 8px !important;
            display: block !important;
            height: 35px !important;
            float: left !important;
            position: relative !important;
            text-decoration: none !important;
            left: 89px !important;
            top: -12px !important;
        }
        body.vertical-armand_gilbert #slides .description a.readmore span {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-readmore.png") no-repeat !important;
            display: block !important;
            height: 35px !important;
            line-height: 32px !important;
            padding: 0px 12px 0px 20px !important;
        }
        body.vertical-armand_gilbert #slides .description a.readmore:hover {
            color: #eeeeee !important;
        }

        /* Controllers */
        body.vertical-armand_gilbert #controllers-wrapper {
            position: absolute !important;
            bottom: 11px !important;
            left: 380px !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-controllers-left.png") no-repeat !important;
            height: 44px !important;
            padding-left: 12px !important;
            z-index: 30 !important;
        }
        body.vertical-armand_gilbert #controllers-wrapper #controllers {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-controllers-bg.png") repeat-x !important;
            height: 30px !important;
            padding-top: 14px !important;
            display: flex !important;
            align-items: center !important;
        }
        body.vertical-armand_gilbert #controllers-wrapper a {
            text-indent: -9999px !important;
            display: block !important;
            float: left !important;
            width: 15px !important;
            height: 15px !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-controller.png") no-repeat !important;
            margin-right: 3px !important;
        }
        body.vertical-armand_gilbert #controllers-wrapper a.active {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/featured-controller-active.png") no-repeat !important;
        }

        /* Content Area & Columns */
        body.vertical-armand_gilbert #content-area {
            width: 960px !important;
            padding: 38px 0px !important;
            margin: 0 auto !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/sidebar-bg.png") 688px 0px repeat-y !important;
            display: flex !important;
            justify-content: space-between !important;
            position: relative !important;
        }
        body.vertical-armand_gilbert #left-area {
            width: 688px !important;
            flex-shrink: 0 !important;
            box-sizing: border-box !important;
            padding-right: 40px !important;
            text-align: left !important;
        }
        body.vertical-armand_gilbert #sidebar {
            width: 269px !important;
            flex-shrink: 0 !important;
            box-sizing: border-box !important;
            padding-left: 20px !important;
            text-align: left !important;
        }

        /* Blog Post Entries Layout */
        body.vertical-armand_gilbert .entry {
            margin-bottom: 45px !important;
            display: flex !important;
            align-items: flex-start !important;
            border: none !important;
            padding: 0 !important;
            text-align: left !important;
        }
        body.vertical-armand_gilbert .blog-thumb {
            flex-shrink: 0 !important;
            width: 185px !important;
            height: 185px !important;
            margin-right: 20px !important;
            border: 3px solid #e5e5e5 !important;
            overflow: hidden !important;
            border-radius: 0px !important;
            background: #ffffff !important;
        }
        body.vertical-armand_gilbert .blog-thumb img {
            width: 100% !important;
            height: 100% !important;
            object-fit: cover !important;
            border: none !important;
        }
        body.vertical-armand_gilbert .entry-description {
            flex-grow: 1 !important;
            width: 443px !important;
            text-align: left !important;
        }
        body.vertical-armand_gilbert .entry h2.title,
        body.vertical-armand_gilbert .entry h1.title {
            font-size: 26px !important;
            padding-bottom: 5px !important;
            margin: 0 0 5px 0 !important;
            text-shadow: none !important;
            color: #332b24 !important;
        }
        body.vertical-armand_gilbert .entry h2.title a,
        body.vertical-armand_gilbert .entry h1.title a {
            color: #332b24 !important;
        }
        body.vertical-armand_gilbert .entry h2.title a:hover {
            color: #986c04 !important;
            text-decoration: none !important;
        }
        body.vertical-armand_gilbert .entry-description p.post-meta {
            display: none !important;
        }
        body.vertical-armand_gilbert .entry-description p {
            color: #333333 !important;
            font-size: 13px !important;
            line-height: 20px !important;
            margin: 0 0 10px 0 !important;
        }

        /* Readmore Button */
        body.vertical-armand_gilbert a.readmore {
            float: right !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/readmore.png") no-repeat bottom right !important;
            height: 38px !important;
            display: block !important;
            font-size: 18px !important;
            color: #323232 !important;
            padding-right: 9px !important;
            margin-top: 14px !important;
            font-weight: normal !important;
            text-shadow: 1px 1px 0px #fff !important;
            font-family: 'ColaborateThinRegular', Arial, sans-serif !important;
        }
        body.vertical-armand_gilbert a.readmore span {
            display: block !important;
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/readmore.png") no-repeat !important;
            padding: 7px 5px 4px 12px !important;
            height: 38px !important;
        }
        body.vertical-armand_gilbert a.readmore:hover {
            color: #ffffff !important;
            text-decoration: none !important;
        }

        /* Sidebar styles */
        body.vertical-armand_gilbert #sidebar .widget {
            margin-bottom: 30px !important;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            border-radius: 0px !important;
        }
        body.vertical-armand_gilbert #sidebar h4 {
            font-size: 18px !important;
            font-weight: normal !important;
            border: none !important;
            padding-bottom: 5px !important;
            margin-bottom: 15px !important;
            color: #332b24 !important;
            text-transform: none !important;
            text-shadow: 1px 1px 0px #fff !important;
        }
        body.vertical-armand_gilbert #sidebar ul {
            list-style: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        body.vertical-armand_gilbert #sidebar ul li {
            padding: 8px 0 !important;
            border-bottom: 1px solid #e2e2e2 !important;
            font-size: 13px !important;
        }
        body.vertical-armand_gilbert #sidebar ul li a {
            color: #332b24 !important;
        }
        body.vertical-armand_gilbert #sidebar ul li a:hover {
            color: #986c04 !important;
        }

        /* Footer */
        body.vertical-armand_gilbert #footer {
            width: 1280px !important;
            height: 63px !important;
            background: url("https://www.armandgilbert.com/wp-content/uploads/2016/11/brown-background.jpg") repeat !important;
            padding: 0px 0px 15px !important;
            margin: 0 auto !important;
            border: none !important;
            z-index: 5 !important;
            position: relative !important;
        }
        body.vertical-armand_gilbert #footer-wrapper {
            background: url("https://armandgilbert.com/wp-content/themes/DeepFocus/images/light-overlay.png") repeat-x !important;
            width: 100% !important;
            height: 100% !important;
        }
        body.vertical-armand_gilbert #footer-center {
            width: 960px !important;
            margin: 0 auto !important;
            padding-top: 20px !important;
        }
        body.vertical-armand_gilbert #copyright {
            color: #ffffff !important;
            font-size: 12px !important;
            text-shadow: 1px 1px 1px #000000 !important;
            margin: 0 !important;
        }
        body.vertical-armand_gilbert #copyright a {
            color: #ffffff !important;
            font-weight: bold !important;
        }
        body.vertical-armand_gilbert #copyright a:hover {
            color: #986c04 !important;
        }

        /* Subpage main elements */
        body.vertical-armand_gilbert .entry-content {
            color: #333333 !important;
            text-align: left !important;
        }
        body.vertical-armand_gilbert .entry-content h1,
        body.vertical-armand_gilbert .entry-content h2,
        body.vertical-armand_gilbert .entry-content h3 {
            font-size: 32px !important;
            margin-top: 20px !important;
            margin-bottom: 15px !important;
            color: #332b24 !important;
        }
        body.vertical-armand_gilbert .entry-content p {
            margin-bottom: 15px !important;
        }

        /* Light form inputs for subpages */
        body.vertical-armand_gilbert form input[type="text"],
        body.vertical-armand_gilbert form input[type="email"],
        body.vertical-armand_gilbert form input[type="tel"],
        body.vertical-armand_gilbert form input[type="url"],
        body.vertical-armand_gilbert form select,
        body.vertical-armand_gilbert form textarea {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
            border-radius: 4px !important;
            color: #333333 !important;
            padding: 8px 12px !important;
            font-size: 13px !important;
            width: 100% !important;
            box-sizing: border-box;
        }
        body.vertical-armand_gilbert form input:focus,
        body.vertical-armand_gilbert form textarea:focus {
            border-color: #986c04 !important;
            box-shadow: 0 0 5px rgba(152, 108, 4, 0.2) !important;
        }
        body.vertical-armand_gilbert form input[type="submit"],
        body.vertical-armand_gilbert form button {
            background-color: #986c04 !important;
            border: none !important;
            color: #ffffff !important;
            padding: 10px 20px !important;
            font-weight: bold !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            text-transform: uppercase !important;
            font-size: 12px !important;
            transition: background-color 0.2s !important;
        }
        body.vertical-armand_gilbert form input[type="submit"]:hover,
        body.vertical-armand_gilbert form button:hover {
            background-color: #c68a0c !important;
        }

        /* Tables on subpages */
        body.vertical-armand_gilbert table {
            width: 100%;
            margin-bottom: 20px;
            border: 1px solid #dddddd;
            border-collapse: collapse;
        }
        body.vertical-armand_gilbert th, body.vertical-armand_gilbert td {
            padding: 10px;
            border: 1px solid #dddddd;
            text-align: left;
        }
        body.vertical-armand_gilbert th {
            background-color: #f5f5f5;
            color: #333333 !important;
            font-weight: bold;
        }
        body.vertical-armand_gilbert tr:nth-child(even) {
            background-color: #fafafa;
        }

        /* Testimonials tabs slider */
        body.vertical-armand_gilbert .tabs-left {
            display: flex;
            background: #1a1a1a;
            border: 1px solid #2c2c2c;
            border-radius: 6px;
            overflow: hidden;
            margin: 30px 0;
            min-height: 250px;
        }
        body.vertical-armand_gilbert .et_left_tabs_bg {
            display: none;
        }
        body.vertical-armand_gilbert .et-tabs-control {
            width: 220px;
            list-style: none !important;
            padding: 0 !important;
            margin: 0 !important;
            border-right: 1px solid #2c2c2c;
            background: #161616;
            flex-shrink: 0;
        }
        body.vertical-armand_gilbert .et-tabs-control li {
            padding: 0 !important;
            margin: 0 !important;
            border-bottom: 1px solid #222;
        }
        body.vertical-armand_gilbert .et-tabs-control li a {
            display: block;
            padding: 15px 20px !important;
            color: #bfbfbf !important;
            font-weight: bold;
            font-size: 12px !important;
            text-decoration: none !important;
            background: transparent;
            border: none !important;
            text-align: left;
        }
        body.vertical-armand_gilbert .et-tabs-control li.active-tab a {
            background: #1a1a1a;
            color: #986c04 !important;
        }
        body.vertical-armand_gilbert .et-tabs-control li a:hover {
            background: #1e1e1e;
            color: #986c04 !important;
        }
        body.vertical-armand_gilbert .et-tabs-content {
            flex-grow: 1;
            padding: 25px;
            position: relative;
            background: #1a1a1a;
        }
        body.vertical-armand_gilbert .et-tabs-content-main-wrap,
        body.vertical-armand_gilbert .et-tabs-content-wrapper {
            height: 100%;
        }
        body.vertical-armand_gilbert .et_slidecontent {
            display: none;
            animation: fadeIn 0.3s ease;
            text-align: left;
        }
        body.vertical-armand_gilbert .et_slidecontent.active-slide {
            display: block;
        }
        body.vertical-armand_gilbert .et_slidecontent img {
            float: left;
            margin: 0 20px 15px 0;
            border: 3px solid #2c2c2c;
            border-radius: 4px;
            max-width: 150px;
            height: auto;
        }


        /* --- DESIGN STYLE PRESET OVERRIDES --- */
        
        /* 1. Modern Minimalist */
        body.design-style-modern_minimalist {
            --body-font: 'Inter', sans-serif !important;
            --heading-font: 'Outfit', sans-serif !important;
            background-color: #ffffff !important;
            --wp--preset--color--base: #ffffff !important;
            --wp--style--block-gap: 2rem !important;
        }
        body.design-style-modern_minimalist .wp-block-group,
        body.design-style-modern_minimalist .wp-block-column {
            border-radius: 4px !important;
            border: 1px solid #f1f5f9 !important;
            box-shadow: none !important;
        }

        /* 2. Dark Sleek */
        body.design-style-dark_sleek {
            --body-font: 'Inter', sans-serif !important;
            --heading-font: 'Outfit', sans-serif !important;
            background-color: #09090b !important;
            color: #e4e4e7 !important;
            
            --wp--preset--color--base: #09090b !important;
            --wp--preset--color--contrast: #ffffff !important;
            --wp--preset--color--accent-2: #18181b !important;
            --wp--preset--color--accent-3: #27272a !important;
            --wp--preset--color--accent-4: #a1a1aa !important;
        }
        body.design-style-dark_sleek h1,
        body.design-style-dark_sleek h2,
        body.design-style-dark_sleek h3,
        body.design-style-dark_sleek h4,
        body.design-style-dark_sleek h5,
        body.design-style-dark_sleek h6,
        body.design-style-dark_sleek .wp-block-site-title a {
            color: #ffffff !important;
        }
        body.design-style-dark_sleek p,
        body.design-style-dark_sleek li,
        body.design-style-dark_sleek figcaption {
            color: #a1a1aa !important;
        }
        body.design-style-dark_sleek .wp-block-group,
        body.design-style-dark_sleek .wp-block-column {
            border-radius: 12px !important;
            background-color: #161619 !important;
            border: 1px solid #27272a !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        }
        body.design-style-dark_sleek .premium-glass-card,
        body.design-style-dark_sleek .wp-block-group.has-background {
            background: rgba(22, 22, 25, 0.7) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        /* 3. Warm Editorial */
        body.design-style-warm_editorial {
            --body-font: 'Inter', sans-serif !important;
            --heading-font: 'Playfair Display', Georgia, serif !important;
            background-color: #fdfaf7 !important;
            color: #44403c !important;
            
            --wp--preset--color--base: #fdfaf7 !important;
            --wp--preset--color--contrast: #292524 !important;
            --wp--preset--color--accent-2: #f5f5f4 !important;
            --wp--preset--color--accent-3: #e7e5e4 !important;
            --wp--preset--color--accent-4: #a8a29e !important;
        }
        body.design-style-warm_editorial .wp-block-group,
        body.design-style-warm_editorial .wp-block-column {
            border-radius: 20px !important;
            border: 1px solid #e7e5e4 !important;
            box-shadow: 0 8px 24px rgba(68,64,60,0.03) !important;
        }

        /* 4. Corporate Tech */
        body.design-style-corporate_tech {
            --body-font: 'Inter', sans-serif !important;
            --heading-font: 'Inter', sans-serif !important;
            background-color: #ffffff !important;
            color: #334155 !important;
            
            --wp--preset--color--base: #ffffff !important;
            --wp--preset--color--contrast: #0f172a !important;
            --wp--preset--color--accent-2: #f8fafc !important;
            --wp--preset--color--accent-3: #e2e8f0 !important;
        }
        body.design-style-corporate_tech .wp-block-group,
        body.design-style-corporate_tech .wp-block-column {
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }

        /* 5. Bold Creative */
        body.design-style-bold_creative {
            --body-font: 'Inter', sans-serif !important;
            --heading-font: 'Outfit', sans-serif !important;
            background-color: #ffffff !important;
            --wp--preset--color--base: #ffffff !important;
            --wp--preset--color--contrast: #000000 !important;
        }
        body.design-style-bold_creative h1,
        body.design-style-bold_creative h2,
        body.design-style-bold_creative h3,
        body.design-style-bold_creative h4 {
            font-weight: 900 !important;
            text-transform: uppercase !important;
            letter-spacing: -1px !important;
        }
        body.design-style-bold_creative .wp-block-group,
        body.design-style-bold_creative .wp-block-column {
            border-radius: 0px !important;
            border: 3px solid #000000 !important;
            box-shadow: 6px 6px 0px #000000 !important;
        }

        /* 6. Classic Elegant */
        body.design-style-classic_elegant {
            --body-font: 'Inter', sans-serif !important;
            --heading-font: 'Playfair Display', Georgia, serif !important;
            background-color: #fafaf9 !important;
            color: #1c1917 !important;
            --wp--preset--color--base: #fafaf9 !important;
            --wp--preset--color--contrast: #1c1917 !important;
        }
        body.design-style-classic_elegant .wp-block-group,
        body.design-style-classic_elegant .wp-block-column {
            border-radius: 0px !important;
            border-top: 1px solid #d6d3d1 !important;
            border-bottom: 1px solid #d6d3d1 !important;
            border-left: none !important;
            border-right: none !important;
            box-shadow: none !important;
        }

        /* Block Border-Radius & Subtle Shadows */
        .wp-block-column {
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        /* Premium Card Styling for Groups/Columns with background */
        .wp-block-group.has-background,
        .wp-block-column.has-background,
        .wp-block-group.premium-card {
            border-radius: 16px !important;
            padding: 40px 32px !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.02) !important;
            border: 1px solid rgba(0, 0, 0, 0.04) !important;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        body.vertical-tech_saas .wp-block-group.has-background,
        body.vertical-tech_saas .wp-block-column.has-background {
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
        }

        .wp-block-group.has-background:hover,
        .wp-block-column.has-background:hover,
        .wp-block-column:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.06) !important;
            border-color: rgba(0, 0, 0, 0.08) !important;
        }

        body.vertical-tech_saas .wp-block-group.has-background:hover,
        body.vertical-tech_saas .wp-block-column.has-background:hover {
            border-color: rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5) !important;
        }

        .wp-block-cover {
            border-radius: 16px !important;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04) !important;
            margin-bottom: 2rem !important;
        }

        /* Button Styling */
        .wp-block-button__link {
            font-family: var(--heading-font, 'Outfit', sans-serif) !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            padding: 14px 28px !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08) !important;
            background-color: var(--accent-color, #ea580c) !important;
            color: #ffffff !important;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out !important;
            text-decoration: none !important;
            display: inline-block !important;
            border: none !important;
        }

        .wp-block-button__link:hover {
            background-color: var(--accent-hover, #c2410c) !important;
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
            color: #ffffff !important;
        }

        /* Premium Menu & Navigation Layout */
        .wp-block-navigation {
            font-family: var(--heading-font, 'Outfit', sans-serif) !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
        }

        .wp-block-navigation-item__content {
            color: var(--wp--preset--color--contrast, #475569) !important;
            padding: 8px 16px !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }

        .wp-block-navigation-item__content:hover {
            color: var(--accent-color, #0f172a) !important;
            background-color: var(--wp--preset--color--accent-2, rgba(0, 0, 0, 0.04)) !important;
        }

        /* Layout width centering & page wrapper */
        .entry-content {
            width: 100% !important;
            max-width: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Override constrained layout width to preserve layout widths */
        .is-layout-constrained > :where(:not(.alignleft):not(.alignright):not(.alignfull)) {
            max-width: 1100px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        header.wp-block-template-part {
            max-width: 1100px !important;
            margin: 0 auto !important;
            padding: 24px !important;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
        }
        body.vertical-tech_saas header.wp-block-template-part {
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        .wp-block-site-title a {
            font-size: 1.5rem !important;
            font-weight: 800 !important;
            color: var(--wp--preset--color--contrast, #0f172a) !important;
            text-decoration: none !important;
            letter-spacing: -0.5px !important;
        }

        /* Footer layout polishing */
        footer.wp-block-template-part {
            max-width: 1100px !important;
            margin: 0 auto !important;
            padding: 48px 24px !important;
            border-top: 1px solid rgba(0, 0, 0, 0.05) !important;
            color: #64748b !important;
        }
        body.vertical-tech_saas footer.wp-block-template-part {
            border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        /* Premium Interactive Form Styles */
        form {
            display: flex;
            flex-direction: column;
            gap: 20px;
            width: 100%;
        }

        form label {
            font-family: var(--heading-font, 'Outfit', sans-serif);
            font-weight: 700;
            font-size: 0.85rem;
            color: var(--wp--preset--color--contrast, #1e293b);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            display: block;
        }

        form input[type="text"],
        form input[type="email"],
        form input[type="tel"],
        form select,
        form textarea {
            width: 100%;
            padding: 14px 18px !important;
            background-color: var(--wp--preset--color--base, #ffffff) !important;
            border: 2px solid var(--wp--preset--color--accent-3, #cbd5e1) !important;
            border-radius: 10px !important;
            color: var(--wp--preset--color--contrast, #1e293b) !important;
            font-family: var(--body-font, 'Inter', sans-serif) !important;
            font-size: 1rem !important;
            outline: none !important;
            transition: border-color 0.2s, box-shadow 0.2s !important;
            box-sizing: border-box;
        }

        body.vertical-tech_saas form input,
        body.vertical-tech_saas form select,
        body.vertical-tech_saas form textarea {
            background-color: var(--wp--preset--color--accent-2, #18181b) !important;
            border-color: var(--wp--preset--color--accent-3, #27272a) !important;
        }

        form input:focus,
        form select:focus,
        form textarea:focus {
            border-color: var(--accent-color, #ea580c) !important;
            box-shadow: 0 0 0 4px var(--wp--preset--color--accent-6) !important;
        }

        form button[type="submit"] {
            background-color: var(--accent-color, #ea580c) !important;
            color: #ffffff !important;
            font-family: var(--heading-font, 'Outfit', sans-serif) !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 16px 32px !important;
            border-radius: 10px !important;
            border: none !important;
            cursor: pointer;
            transition: transform 0.2s, background-color 0.2s, box-shadow 0.2s !important;
        }

        form button[type="submit"]:hover {
            background-color: var(--accent-hover, #c2410c) !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--wp--preset--color--accent-6) !important;
        }

        /* Sticky Premium Top Bar Styling */
        .premium-mockup-top-bar {
            background-color: var(--wp--preset--color--contrast, #1e293b) !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            padding: 8px 24px;
            position: sticky;
            top: 0;
            z-index: 99999;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .top-bar-content {
            max-width: 1100px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }

        .business-badge {
            font-family: var(--heading-font, 'Outfit', sans-serif);
            font-weight: 800;
            letter-spacing: -0.3px;
            font-size: 0.9rem;
            color: var(--accent-color, #ea580c);
            text-transform: uppercase;
        }

        .contact-info {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .contact-link {
            color: #e2e8f0 !important;
            text-decoration: none !important;
            transition: color 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .contact-link:hover {
            color: #ffffff !important;
        }

        .contact-link strong {
            color: #ffffff;
        }

        .top-bar-btn {
            background-color: var(--accent-color, #ea580c) !important;
            color: #ffffff !important;
            text-decoration: none !important;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: 700;
            font-family: var(--heading-font, 'Outfit', sans-serif);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
        }

        .top-bar-btn:hover {
            background-color: var(--accent-hover, #c2410c) !important;
            transform: translateY(-1px);
        }

        @media (max-width: 768px) {
            .top-bar-btn {
                display: none;
            }
            .contact-info {
                gap: 10px;
            }
            .action-label {
                display: none;
            }
        }

        /* ============================================================
           Gravity Forms 1:1 (Armand Gilbert) — layout, labels, progress
           Added to match armandgilbert.com get-started/contact forms.
           ============================================================ */
        body.vertical-armand_gilbert .gform_wrapper form { display: block !important; }

        /* Field list -> 12-col grid, kill theme bullets */
        body.vertical-armand_gilbert .gform_fields {
            display: grid !important;
            grid-template-columns: repeat(12, 1fr) !important;
            grid-column-gap: 20px !important;
            grid-row-gap: 18px !important;
            margin: 0 !important;
            padding: 0 !important;
            list-style: none !important;
        }
        body.vertical-armand_gilbert .gform_fields > li.gfield {
            grid-column: span 12 !important;
            display: block !important;
            list-style: none !important;
            margin: 0 !important;
            padding: 0 !important;
            background: none !important;
        }
        body.vertical-armand_gilbert .gform_fields > li.gfield::before,
        body.vertical-armand_gilbert .gform_fields > li.gfield::marker { content: none !important; display: none !important; }
        body.vertical-armand_gilbert .gfield_radio,
        body.vertical-armand_gilbert .gfield_checkbox {
            list-style: none !important; margin: 0 !important; padding: 0 !important;
        }
        body.vertical-armand_gilbert .gfield_radio li,
        body.vertical-armand_gilbert .gfield_checkbox li {
            list-style: none !important; margin: 0 0 6px !important; padding: 0 !important;
        }

        /* Labels — mixed-case, dark, semi-bold (not all-caps) */
        body.vertical-armand_gilbert .gfield_label,
        body.vertical-armand_gilbert .gform_fields > li.gfield > label {
            text-transform: none !important;
            letter-spacing: normal !important;
            font-family: inherit !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            color: #333 !important;
            margin-bottom: 6px !important;
        }
        body.vertical-armand_gilbert .gfield_required { color: #c00 !important; }
        /* Sublabels (First, Last, City...) — small gray, normal weight */
        body.vertical-armand_gilbert .ginput_complex label {
            text-transform: none !important;
            letter-spacing: normal !important;
            font-weight: normal !important;
            font-size: 12px !important;
            color: #888 !important;
            margin-top: 4px !important;
        }

        /* Internal multi-column rows (name / address) */
        body.vertical-armand_gilbert .gform-grid-row {
            display: flex !important; flex-wrap: wrap !important; gap: 16px !important; margin: 0 !important;
        }
        body.vertical-armand_gilbert .gform-grid-row > .gform-grid-col { padding: 0 !important; min-width: 0 !important; }
        body.vertical-armand_gilbert .ginput_full { flex: 1 1 100% !important; }
        body.vertical-armand_gilbert .name_first,
        body.vertical-armand_gilbert .name_last,
        body.vertical-armand_gilbert .ginput_left,
        body.vertical-armand_gilbert .ginput_right { flex: 1 1 calc(50% - 8px) !important; }
        body.vertical-armand_gilbert .gf_clear,
        body.vertical-armand_gilbert .gf_clear_complex { display: none !important; }

        /* Inputs — plain rectangular, thin gray border */
        body.vertical-armand_gilbert .gform_wrapper input[type="text"],
        body.vertical-armand_gilbert .gform_wrapper input[type="email"],
        body.vertical-armand_gilbert .gform_wrapper input[type="tel"],
        body.vertical-armand_gilbert .gform_wrapper input[type="url"],
        body.vertical-armand_gilbert .gform_wrapper select,
        body.vertical-armand_gilbert .gform_wrapper textarea {
            width: 100% !important;
            padding: 8px 9px !important;
            border: 1px solid #c8c8c8 !important;
            border-radius: 0 !important;
            background: #fff !important;
            font-size: 14px !important;
            box-shadow: inset 1px 1px 2px rgba(0,0,0,0.05) !important;
            box-sizing: border-box !important;
        }

        /* Section break heading (e.g. WEB DESIGN QUESTIONNAIRE 1 of 4) */
        body.vertical-armand_gilbert .gsection {
            border-bottom: 1px solid #ddd !important;
            margin: 10px 0 4px !important;
            padding: 0 0 6px !important;
        }
        body.vertical-armand_gilbert .gform_wrapper h2.gsection_title,
        body.vertical-armand_gilbert .gform_wrapper .gsection_title,
        body.vertical-armand_gilbert .gsection .gfield_label {
            text-transform: none !important;
            font-weight: normal !important;
            font-size: 22px !important;
            line-height: 1.3 !important;
            color: #aaaaaa !important;
            margin: 0 !important;
        }

        /* Progress bar — blue filled rounded bar */
        body.vertical-armand_gilbert .gf_progressbar_title {
            font-size: 13px !important; font-weight: normal !important;
            text-transform: none !important; color: #888 !important; margin: 0 0 6px !important;
        }
        body.vertical-armand_gilbert .gf_progressbar {
            background: #dfe3e8 !important; border-radius: 12px !important;
            height: 24px !important; padding: 0 !important; overflow: hidden !important; box-shadow: none !important;
        }
        body.vertical-armand_gilbert .gf_progressbar_percentage {
            height: 100% !important; background: #2980d8 !important; color: #fff !important;
            font-size: 13px !important; font-weight: bold !important; line-height: 24px !important;
            text-align: center !important; border-radius: 12px !important;
        }
        body.vertical-armand_gilbert .percentbar_0 { width: 0 !important; }
        body.vertical-armand_gilbert .percentbar_25 { width: 25% !important; }
        body.vertical-armand_gilbert .percentbar_50 { width: 50% !important; }
        body.vertical-armand_gilbert .percentbar_75 { width: 75% !important; }
        body.vertical-armand_gilbert .percentbar_100 { width: 100% !important; }

        /* Multi-step nav buttons — plain (original Next button is default-style) */
        body.vertical-armand_gilbert .gform_wrapper .gform_next_button,
        body.vertical-armand_gilbert .gform_wrapper .gform_previous_button {
            background: #f5f5f5 !important; color: #333 !important;
            border: 1px solid #bbb !important; border-radius: 3px !important;
            text-transform: none !important; font-weight: normal !important;
            font-size: 14px !important; letter-spacing: normal !important; padding: 4px 12px !important;
        }
    </style>
    <?php
});

// Dynamic sticky top contact bar injector
add_action('wp_body_open', function() {
    $vertical = get_option('wp_mockup_vertical', 'general');
    if ($vertical === 'armand_gilbert') {
        return;
    }
    $phone = get_option('wp_mockup_phone');
    $email = get_option('wp_mockup_email');
    $business_name = get_option('wp_mockup_business_name', get_bloginfo('name'));

    if (!$phone && !$email) {
        return; // Nothing to show
    }

    // Determine banner action text based on vertical
    $action_text = "Call Now";
    $btn_text = "Get Estimate";
    if ($vertical === 'health_wellness') {
        $action_text = "Book Appointment";
        $btn_text = "Book Online";
    } elseif ($vertical === 'restaurant_food') {
        $action_text = "Reserve Table";
        $btn_text = "Book Reservation";
    } elseif ($vertical === 'tech_saas') {
        $action_text = "Get Started";
        $btn_text = "Get Demo";
    } elseif ($vertical === 'medical_professional') {
        $action_text = "Schedule Consultation";
        $btn_text = "Book Appointment";
    }

    ?>
    <div class="premium-mockup-top-bar">
        <div class="top-bar-content">
            <span class="business-badge"><?php echo esc_html($business_name); ?></span>
            <div class="contact-info">
                <?php if ($phone): ?>
                    <a href="tel:<?php echo esc_attr(preg_replace('/[^0-9+]/', '', $phone)); ?>" class="contact-link phone-link">
                        📞 <span class="action-label"><?php echo esc_html($action_text); ?>:</span> <strong><?php echo esc_html($phone); ?></strong>
                    </a>
                <?php endif; ?>
                <?php if ($email): ?>
                    <a href="mailto:<?php echo esc_attr($email); ?>" class="contact-link email-link">
                        ✉️ <span><?php echo esc_html($email); ?></span>
                    </a>
                <?php endif; ?>
            </div>
            <div class="top-bar-actions">
                <?php if ($phone): ?>
                    <a href="tel:<?php echo esc_attr(preg_replace('/[^0-9+]/', '', $phone)); ?>" class="top-bar-btn">
                        <?php echo esc_html($btn_text); ?>
                    </a>
                <?php endif; ?>
            </div>
        </div>
    </div>
    <?php
});

// Dynamic vertical & design style body class injector
add_action('body_class', function($classes) {
    $vertical = get_option('wp_mockup_vertical', 'general');
    $classes[] = 'vertical-' . $vertical;
    if ($vertical !== 'armand_gilbert') {
        $design_style = get_option('wp_mockup_design_style', 'modern_minimalist');
        $classes[] = 'design-style-' . $design_style;
    }
    return $classes;
});

// Slider Controller for Armand Gilbert 1:1 Replica
add_action('wp_footer', function() {
    $vertical = get_option('wp_mockup_vertical', 'general');
    if ($vertical !== 'armand_gilbert') {
        return;
    }
    ?>
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        const slides = document.querySelectorAll(".slide");
        const dots = document.querySelectorAll("#controllers a");
        if (slides.length > 0) {
            let activeIndex = 0;
            let intervalId = null;

            function showSlide(index) {
                slides.forEach(s => s.classList.remove("active"));
                dots.forEach(d => d.classList.remove("active"));
                slides[index].classList.add("active");
                dots[index].classList.add("active");
                activeIndex = index;
            }

            function nextSlide() {
                let nextIndex = (activeIndex + 1) % slides.length;
                showSlide(nextIndex);
            }

            function startAutoPlay() {
                intervalId = setInterval(nextSlide, 5000);
            }

            function stopAutoPlay() {
                clearInterval(intervalId);
            }

            dots.forEach((dot, idx) => {
                dot.addEventListener("click", function(e) {
                    e.preventDefault();
                    stopAutoPlay();
                    showSlide(idx);
                    startAutoPlay();
                });
            });

            startAutoPlay();
        }

        // Testimonials tab switcher
        const containers = document.querySelectorAll(".tabs-left");
        containers.forEach(container => {
            const tabs = container.querySelectorAll(".et-tabs-control li");
            const slidesList = container.querySelectorAll(".et_slidecontent");
            if (tabs.length === 0 || slidesList.length === 0) return;
            
            // Set initial active states
            tabs[0].classList.add("active-tab");
            slidesList[0].classList.add("active-slide");
            
            tabs.forEach((tab, idx) => {
                const link = tab.querySelector("a");
                if (!link) return;
                link.addEventListener("click", function(e) {
                    e.preventDefault();
                    tabs.forEach(t => t.classList.remove("active-tab"));
                    slidesList.forEach(s => s.classList.remove("active-slide"));
                    
                    tab.classList.add("active-tab");
                    if (slidesList[idx]) {
                        slidesList[idx].classList.add("active-slide");
                    }
                });
            });
        });
    });
    </script>
    <?php
});

