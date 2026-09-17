# Eskimo — Webflow class reference

Generated from `eskimo-home.html` and `eskimo-features-lead-management.html`.
Regenerate after every build so rule 1 (reuse, don't reinvent) can be checked against real values.

**Conventions**
- Client-First V2: `folder_element` for components, hyphens within names, `is-` for combo modifiers.
- Nothing bare or single-word. Project-specific components are prefixed `eskimo-`.
- Every `is-` modifier is written scoped to its base (`.base.is-modifier`), never standalone.


## Layout globals (Client-First)

| Class | Key CSS |
|---|---|
| `.page-wrapper` | position: relative; background-color: #FFFFFF |
| `.padding-global` | padding-left: 3.378rem; padding-right: 3.378rem |
| `.container-large` | width: 100%; max-width: 71.37rem |
| `.container-medium` | width: 100%; max-width: 64.875rem |
| `.padding-section-large` | padding-top: 7.5rem; padding-bottom: 7.5rem |
| `.padding-section-large.is-faq` | padding-top: 7.5rem; padding-bottom: 7.4394rem |
| `.padding-section-large.is-features` | padding-top: 7.5rem; padding-bottom: 8.75rem |
| `.padding-section-large.is-footer` | padding-top: 7.5rem; padding-bottom: 2.1813rem |
| `.padding-section-large.is-hero` | padding-top: 8.125rem; padding-bottom: 4.8606rem |
| `.padding-section-large.is-hero-sub` | padding-top: 8.125rem; padding-bottom: 6.075rem |
| `.padding-section-large.is-highlights` | padding-top: 0; padding-bottom: 6.875rem |
| `.padding-section-large.is-integrations` | padding-top: 7.5rem; padding-bottom: 8.9438rem |
| `.padding-section-large.is-integrations-tall` | padding-top: 7.5rem; padding-bottom: 10.9088rem |
| `.padding-section-large.is-stories` | padding-top: 7.5rem; padding-bottom: 8.7469rem |
| `.padding-section-large.is-stories-compact` | padding-top: 7.5rem; padding-bottom: 8.3756rem |
| `.padding-section-large.is-tools` | padding-top: 6.7838rem; padding-bottom: 6.875rem |
| `.padding-section-large.is-who` | padding-top: 7.5rem; padding-bottom: 8.8163rem |

## Typography globals (Client-First)

| Class | Key CSS |
|---|---|
| `.heading-style-h1` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 4rem; line-height: 4.25rem; letter-spacing: -0.04em |
| `.heading-style-h2` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 2.75rem; line-height: 3rem; letter-spacing: -0.04em |
| `.heading-style-h3` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 2rem; line-height: 2.25rem; letter-spacing: -0.03em |
| `.heading-style-h4` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 1.5rem; line-height: 1.75rem; letter-spacing: -0.03em |
| `.text-size-large` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 1.25rem; line-height: 1.625rem; letter-spacing: -0.01em |
| `.text-size-regular` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 1rem; line-height: 1.5rem; letter-spacing: -0.01em |
| `.text-size-small` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 0.875rem; line-height: 0.875rem; letter-spacing: -0.02em |
| `.text-size-tiny` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 0.75rem; line-height: 1rem; letter-spacing: 0 |
| `.text-weight-medium` | font-weight: 500 |
| `.text-weight-bold` | font-weight: 700 |
| `.text-color-white` | color: #FFFFFF |
| `.text-color-dark` | color: #111313 |
| `.text-color-blue` | color: #0875E1 |
| `.text-color-body` | color: #4F5863 |
| `.text-color-tint` | color: #DDEEFF |
| `.text-align-center` | text-align: center |

## Shared components

| Class | Key CSS |
|---|---|
| `.eskimo-button` | display: inline-flex; align-items: center; justify-content: center; height: 2.8125rem |
| `.eskimo-button.is-secondary` | background-color: transparent; color: #FFFFFF |
| `.eskimo-button.is-secondary:active` | background-color: rgba(255, 255, 255, 0.2); transform: translateY(0.0625rem) scale(0.985) |
| `.eskimo-button.is-secondary:focus-visible` | — |
| `.eskimo-button.is-secondary:hover` | background-color: rgba(255, 255, 255, 0.12) |
| `.eskimo-tag` | display: inline-flex; align-items: center; justify-content: center; height: 2.1875rem |
| `.eskimo-tag.is-blue` | background-color: rgba(221, 238, 255, 0.2) |
| `.eskimo-tag.is-ghost` | background-color: rgba(255, 255, 255, 0.1) |
| `.eskimo-tag.is-hero` | background-color: rgba(255, 255, 255, 0.1); gap: 0.4039rem |
| `.eskimo-tag.is-round` | border-radius: 0.625rem |
| `.eskimo-tag_text` | font-weight: 700 |
| `.eskimo-tag_icon` | display: block |
| `.eskimo-tag_icon.is-hero` | width: 1.0268rem; height: 0.6333rem |
| `.eskimo-tag_icon.is-people` | width: 0.9375rem; height: 0.7248rem |
| `.eskimo-tag_icon.is-person` | width: 0.6989rem; height: 0.6657rem |
| `.eskimo-tag_icon.is-play` | width: 0.6744rem; height: 0.68rem |
| `.eskimo-tag_icon.is-quote` | width: 0.75rem; height: 0.5994rem |
| `.eskimo-tag_icon.is-square` | width: 0.7063rem; height: 0.7063rem |
| `.eskimo-tag_icon.is-stack` | width: 0.5319rem; height: 0.7038rem |
| `.link-read-more` | display: inline-flex; align-items: center; gap: 0.4894rem; padding-bottom: 0.2644rem |
| `.link-read-more.is-light` | color: #FFFFFF |
| `.link-read-more.is-light:focus-visible` | — |
| `.link-read-more.is-light:hover` | color: #DDEEFF |
| `.link-read-more_label` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 0.875rem; line-height: 0.875rem; letter-spacing: -0.02em |
| `.link-read-more_icon` | display: block; width: 0.1292rem; height: 0.2907rem |
| `.collage_item` | position: absolute; display: block; height: auto; filter: drop-shadow(0 0.3125rem 0.9375rem rgba(106, 114, 130, 0.2)) |
| `.collage_item.is-feat-autotrader` | left: 0; top: 73.505%; width: 34.984%; aspect-ratio: 220 / 80 |
| `.collage_item.is-feat-calls` | left: 69.469%; top: 77.712%; width: 12.045%; aspect-ratio: 75.748 / 75 |
| `.collage_item.is-feat-cars` | left: 69.469%; top: 20.674%; width: 30.531%; aspect-ratio: 192 / 240 |
| `.collage_item.is-feat-messenger` | left: 87.955%; top: 0; width: 12.045%; aspect-ratio: 75.748 / 75 |
| `.collage_item.is-feat-mobile` | left: 21.934%; top: 9.978%; width: 43.411%; aspect-ratio: 273 / 426 |
| `.collage_item.is-home-autotrader` | left: 0; top: 20.486%; width: 19.259%; aspect-ratio: 220 / 80 |
| `.collage_item.is-home-calls` | left: 0.008%; top: 0; width: 6.631%; aspect-ratio: 75.748 / 75 |
| `.collage_item.is-home-cars` | left: 25.256%; top: 28.104%; width: 16.807%; aspect-ratio: 192 / 240 |
| `.collage_item.is-home-customers` | left: 76.254%; top: 22.552%; width: 19.259%; aspect-ratio: 220 / 80 |
| `.collage_item.is-home-dash` | left: 9.086%; top: 36.987%; width: 54.799%; aspect-ratio: 626 / 426 |
| `.collage_item.is-home-messenger` | left: 93.369%; top: 5.621%; width: 6.631%; aspect-ratio: 75.748 / 75 |
| `.collage_item.is-home-mobile` | left: 66.849%; top: 36.987%; width: 23.898%; aspect-ratio: 273 / 426 |
| `.collage_item.is-home-web-enquiry` | left: 25.386%; top: 76.909%; width: 19.259%; aspect-ratio: 220 / 80 |
| `.collage_item.is-home-whatsapp` | left: 48.585%; top: 54.528%; width: 19.259%; aspect-ratio: 220 / 80 |
| `.collage_item.is-lm-autotrader` | left: 0; top: 1.742%; width: 19.474%; aspect-ratio: 220 / 80 |
| `.collage_item.is-lm-calls` | left: 9.164%; top: 22.268%; width: 6.705%; aspect-ratio: 75.748 / 75 |
| `.collage_item.is-lm-customers` | left: 10.304%; top: 64.740%; width: 19.474%; aspect-ratio: 220 / 80 |
| `.collage_item.is-lm-customers-2` | left: 70.789%; top: 69.300%; width: 19.474%; aspect-ratio: 220 / 80 |
| `.collage_item.is-lm-dash` | left: 22.534%; top: 26.413%; width: 55.412%; aspect-ratio: 626 / 426 |
| `.collage_item.is-lm-messenger` | left: 83.558%; top: 21.490%; width: 6.705%; aspect-ratio: 75.748 / 75 |
| `.collage_item.is-lm-record` | left: 33.245%; top: 19.294%; width: 33.991%; aspect-ratio: 384 / 206.349 |
| `.collage_item.is-lm-whatsapp` | left: 80.526%; top: 0; width: 19.474%; aspect-ratio: 220 / 80 |

## Nav (shared)

| Class | Key CSS |
|---|---|
| `.section_nav` | position: absolute; top: 1.875rem; left: 0; z-index: 20 |
| `.nav_component` | display: flex; align-items: center; height: 2.5rem |
| `.nav_brand` | display: flex; align-items: center; gap: 0.6925rem |
| `.nav_brand-mark` | display: block; width: 1.4988rem; height: 1.6875rem |
| `.nav_brand-wordmark` | display: block; width: 5.3025rem; height: 1.2256rem |
| `.nav_menu` | display: flex; align-items: center |
| `.nav_list` | display: flex; align-items: center; gap: 1.875rem; margin: 0 |
| `.nav_item` | display: flex; align-items: center; gap: 0.3938rem |
| `.nav_link` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 0.875rem; line-height: 0.875rem; letter-spacing: -0.02em |
| `.nav_caret` | display: block; width: 0.2813rem; height: 0.125rem |
| `.nav_actions` | display: flex; align-items: center; gap: 0.605rem |
| `.nav_login` | font-family: Manrope, "Helvetica Neue", Arial, sans-serif; font-size: 0.875rem; line-height: 0.875rem; letter-spacing: -0.02em |
| `.nav_menu-button` | display: none; flex-direction: column; justify-content: center; gap: 0.25rem |
| `.nav_menu-bar` | display: block; width: 1.5rem; height: 0.125rem; background-color: #FFFFFF |

## Hero (shared shell)

| Class | Key CSS |
|---|---|
| `.section_hero` | position: relative; z-index: 1; overflow: hidden; background-color: #FFFFFF |
| `.hero_background` | position: absolute; top: 0; left: 0; width: 100% |
| `.hero_gradient` | position: absolute; top: 0; left: 0; width: 100% |
| `.hero_glow` | position: absolute; top: 20.125rem; left: 0; width: 100% |
| `.hero_component` | position: relative; z-index: 1 |
| `.hero_content` | position: relative; z-index: 2; display: flex; flex-direction: column |
| `.hero_content.is-sub` | gap: 0 |
| `.hero_heading-wrapper` | width: 100%; max-width: 51.632rem |
| `.hero_heading-wrapper.is-sub` | max-width: 44.4375rem; margin-top: 0.8681rem |
| `.hero_heading` | color: #FFFFFF |
| `.hero_heading-break` | display: inline |
| `.hero_subheading-wrapper` | width: 100%; max-width: 34.375rem |
| `.hero_subheading-wrapper.is-sub` | max-width: 36.06rem; margin-top: 1.875rem |
| `.hero_subheading` | margin: 0 |
| `.hero_visual` | position: relative; z-index: 1; width: 100%; aspect-ratio: 1142.35 / 676.07 |
| `.hero_visual.is-sub` | max-width: 70.6072rem; aspect-ratio: 1129.715 / 578.911; margin-top: -4.2238rem |
| `.hero_button-wrapper` | margin-top: 1.875rem |
| `.hero_logos` | position: relative; z-index: 1; display: flex; flex-direction: column |
| `.hero_logos-label-wrapper` | width: 100%; max-width: 58.25rem |
| `.hero_logos-label` | margin: 0 |
| `.hero_logos-row` | display: flex; align-items: center; justify-content: center; gap: 4.4954rem |
| `.hero_logo` | display: block |
| `.hero_logo.is-citroen` | width: 6.7194rem; height: 0.6894rem |
| `.hero_logo.is-nissan` | width: 6.7003rem; height: 0.6252rem |
| `.hero_logo.is-opel` | width: 6.7444rem; height: 0.9781rem |

## Features section (shared shell)

| Class | Key CSS |
|---|---|
| `.section_features` | position: relative; z-index: 2; margin-top: -1.25rem; border-radius: 1.25rem 1.25rem 0 0 |
| `.features_component` | position: relative |
| `.features_header` | display: flex; flex-direction: column; align-items: center; gap: 1.875rem |
| `.features_heading-wrapper` | width: 100%; max-width: 58.167rem |
| `.features_heading` | margin: 0 |
| `.features_heading-break` | display: inline |

## Integrations (shared)

| Class | Key CSS |
|---|---|
| `.section_integrations` | position: relative; z-index: 3; margin-top: -1.25rem; border-radius: 1.25rem 1.25rem 0 0 |
| `.integrations_component` | position: relative; display: flex; flex-direction: column; align-items: center |
| `.integrations_float` | position: absolute; display: block; width: 4.7343rem; height: auto |
| `.integrations_float.is-left` | left: 0; top: 1.9606rem |
| `.integrations_float.is-right` | top: 12.4288rem |
| `.integrations_heading-wrapper` | width: 100%; max-width: 58.2544rem; margin-top: 1.875rem |
| `.integrations_heading` | margin: 0 |
| `.integrations_heading-break` | display: inline |
| `.integrations_paragraph-wrapper` | width: 100%; max-width: 45.0044rem; margin-top: 1.875rem |
| `.integrations_paragraph` | margin: 0 |
| `.integrations_grid` | display: grid; grid-template-columns: repeat(5, 1fr); width: 100%; max-width: 51.5044rem |
| `.integrations_cell` | display: flex; align-items: center; justify-content: center; height: 3.4781rem |
| `.integrations_cell.is-col-end` | border-right: 0 |
| `.integrations_cell.is-row-end` | border-bottom: 0 |
| `.integrations_logo` | display: block |
| `.integrations_logo.is-autotrader` | width: 6.07rem; height: 1.3438rem |
| `.integrations_logo.is-facebook` | width: 5.0938rem; height: 0.9869rem |
| `.integrations_logo.is-whatsapp` | width: 5.7956rem; height: 1.7113rem |
| `.integrations_link-wrapper` | margin-top: 2.9456rem |

## Customer stories (shared)

| Class | Key CSS |
|---|---|
| `.section_stories` | position: relative; z-index: 5; margin-top: -1.25rem; border-radius: 1.25rem 1.25rem 0 0 |
| `.stories_component` | position: relative; display: flex; flex-direction: column; align-items: center |
| `.stories_quote-wrapper` | width: 100%; max-width: 57.9531rem; margin-top: 1.875rem |
| `.stories_quote` | margin: 0 |
| `.stories_attribution-wrapper` | margin-top: 1.875rem |
| `.stories_attribution` | margin: 0 |
| `.stories_attribution-name` | font-weight: 700; color: #FFFFFF |
| `.stories_grid` | display: grid; grid-template-columns: 1fr 1fr; gap: 1.125rem; width: 100% |
| `.stories_card` | display: flex; flex-direction: column; min-height: 14.9956rem; padding: 1.9975rem 1.9375rem 2.2575rem 1.9375rem |
| `.stories_card-title` | margin: 0; max-width: 22.7344rem |
| `.stories_card-text` | margin: 1.25rem 0 0 0 |
| `.stories_card-link` | margin-top: auto |
| `.stories_link-wrapper` | margin-top: 5.629rem |

## Footer (shared)

| Class | Key CSS |
|---|---|
| `.section_footer` | position: relative; z-index: 7; margin-top: -1.25rem; border-radius: 1.25rem 1.25rem 0 0 |
| `.footer_component` | position: relative |
| `.footer_cta` | display: flex; align-items: center; justify-content: space-between; gap: 2rem |
| `.footer_cta-text-wrapper` | max-width: 28.5rem |
| `.footer_cta-text` | margin: 0 |
| `.footer_form` | display: flex; align-items: center; gap: 0.4606rem |
| `.footer_input` | width: 22.8281rem; height: 2.8125rem; padding-left: 1.8825rem; padding-right: 1.8825rem |
| `.footer_submit` | width: 6rem |
| `.footer_closing` | display: flex; flex-direction: column; align-items: center; margin-top: 7.4819rem |
| `.footer_closing-heading-wrapper` | width: 100%; max-width: 71.5625rem |
| `.footer_closing-heading` | margin: 0 |
| `.footer_closing-break` | display: inline |
| `.footer_buttons` | display: flex; align-items: center; gap: 1.3438rem; margin-top: 1.8738rem |
| `.footer_top` | display: flex; align-items: flex-start; justify-content: space-between; margin-top: 10.1325rem |
| `.footer_brand` | display: block; padding-top: 0.5688rem |
| `.footer_logo` | display: block; width: 17.875rem; height: 4.0219rem |
| `.footer_nav` | display: flex; gap: 5.8438rem |
| `.footer_column` | — |
| `.footer_column-title` | font-weight: 700; line-height: 1.3125rem |
| `.footer_link-list` | margin: 0; padding: 0 |
| `.footer_link-item` | display: block |
| `.footer_link` | display: block; font-weight: 700; line-height: 1.3125rem; color: #4F5863 |
| `.footer_bottom` | display: flex; align-items: center; justify-content: space-between; margin-top: 7.7031rem |
| `.footer_copyright` | font-weight: 700; color: #4F5863 |
| `.footer_legal-list` | display: flex; align-items: center; gap: 2.25rem; margin: 0 |
| `.footer_legal-item` | display: block |
| `.footer_legal-link` | display: block; font-weight: 700; color: #4F5863 |

## Page 01 only — tabs / who-we-help / FAQ

| Class | Key CSS |
|---|---|
| `.features_tabs-wrapper` | display: flex; justify-content: center; margin-top: 3.75rem |
| `.features_tabs` | display: flex; align-items: center; gap: 2.065rem; width: 100% |
| `.features_tab` | display: inline-flex; align-items: center; height: 2.5rem; padding: 0 |
| `.features_tab.is-active` | background-color: #C7FF3D; color: #111313; padding-left: 1.6706rem; padding-right: 1.6706rem |
| `.features_tab.is-active:hover` | background-color: #B9F52B; color: #111313 |
| `.features_layout` | position: relative; margin-top: 1.9138rem; min-height: 29.5756rem |
| `.features_text` | width: 28.5453rem; padding-top: 6.675rem |
| `.features_subheading` | max-width: 27.2167rem |
| `.features_paragraph` | margin: 1.875rem 0 0 0 |
| `.features_link` | margin-top: 3.75rem |
| `.features_visual` | position: absolute; left: 39.42%; top: 0; width: 60.59% |
| `.section_who` | position: relative; z-index: 4; margin-top: -1.25rem; border-radius: 1.25rem 1.25rem 0 0 |
| `.who_component` | position: relative |
| `.who_header` | display: flex; flex-direction: column; align-items: center; gap: 1.25rem |
| `.who_heading-wrapper` | width: 100%; max-width: 45rem |
| `.who_heading` | margin: 0 |
| `.who_grid` | display: grid; grid-template-columns: 1fr 1fr; column-gap: 1.1573rem; row-gap: 1.875rem |
| `.who_card` | display: flex; flex-direction: column; min-height: 17.9375rem; padding: 2.625rem 1.895rem 2.054rem 1.895rem |
| `.who_card-title` | margin: 0 |
| `.who_card-text` | margin: 0.9375rem 0 0 0; max-width: 26.6048rem |
| `.who_card-link` | margin-top: auto |
| `.section_faq` | position: relative; z-index: 6; margin-top: -1.25rem; border-radius: 1.25rem 1.25rem 0 0 |
| `.faq_component` | display: flex; flex-direction: column; align-items: center |
| `.faq_heading-wrapper` | width: 100%; max-width: 58.2463rem; margin-top: 1.875rem |
| `.faq_heading` | margin: 0 |
| `.faq_heading-break` | display: inline |
| `.faq_list` | width: 100%; max-width: 51.6138rem; margin-top: 3.75rem |
| `.faq_item` | border-bottom: 1px solid #D8DDE2 |
| `.faq_item.is-last` | border-bottom: 0 |
| `.faq_question` | color: #4F5863; display: flex; align-items: center; justify-content: space-between |
| `.faq_question-text` | font-weight: 700; color: inherit |
| `.faq_icon` | display: block; width: 0.2819rem; height: 0.125rem |
| `.faq_icon.is-open` | transform: rotate(180deg) |
| `.faq_answer` | overflow: hidden |
| `.faq_answer.is-open` | — |
| `.faq_answer-text` | margin: 0 0 1.5rem 0; max-width: 43.75rem |

## Page 02 only — highlights / tools grid / in-action

| Class | Key CSS |
|---|---|
| `.section_highlights` | position: relative; z-index: 1; background-color: #FFFFFF |
| `.highlights_grid` | display: grid; grid-template-columns: 1fr 1fr; column-gap: 1.2641rem; row-gap: 1.875rem |
| `.highlights_card` | position: relative; overflow: hidden; min-height: 25rem; padding: 3.3388rem 1.9013rem 0 1.9013rem |
| `.highlights_card-title` | margin: 0; position: relative; z-index: 2 |
| `.highlights_card-text` | margin: 0.9375rem 0 0 0; max-width: 27.609rem; position: relative; z-index: 2 |
| `.highlights_card-screen` | position: absolute; left: 37.365%; top: 43.135%; width: 53.953% |
| `.highlights_card-badge` | position: absolute; left: 7.793%; top: 71.146%; width: 43.478% |
| `.features_grid` | display: grid; grid-template-columns: repeat(3, 1fr); column-gap: 3.275rem; row-gap: 3.75rem |
| `.features_grid-item` | — |
| `.features_item-header` | display: flex; align-items: center; gap: 0.625rem |
| `.features_item-icon` | display: block; width: 1.5625rem; height: 1.5625rem |
| `.features_item-title` | margin: 0 |
| `.features_item-text` | margin: 0.9375rem 0 0 0 |
| `.inaction_panel` | position: relative; overflow: hidden; width: 100%; height: 39.0625rem |
| `.inaction_tag` | margin-top: 5.625rem |
| `.inaction_heading-wrapper` | width: 100%; max-width: 52.0356rem; margin: 1.875rem auto 0 auto |
| `.inaction_heading` | margin: 0 |
| `.inaction_heading-break` | display: inline |
| `.inaction_play` | position: absolute; left: 50%; top: 44.96%; transform: translateX(-50%) |
| `.inaction_play-icon` | display: block; width: 3.125rem; height: 3.125rem |
| `.inaction_screens` | position: absolute; left: 0; top: 50.13%; width: 100% |
| `.inaction_screen` | position: absolute; top: 0; height: auto; display: block |
| `.inaction_screen.is-narrow` | left: 66.800%; width: 23.819%; aspect-ratio: 273 / 426; filter: drop-shadow(0 0.3125rem 0.9375rem rgba(106, 114, 130, 0.2)) |
| `.inaction_screen.is-wide` | left: 9.219%; width: 54.617%; aspect-ratio: 626 / 426; filter: drop-shadow(0 0.3125rem 1.875rem rgba(106, 114, 130, 0.2)) |

## Interaction states (hover / pressed / focused)

| Class | Key CSS |
|---|---|
| `.eskimo-button:active` | background-color: #ACEA1C; transform: translateY(0.0625rem) scale(0.985) |
| `.eskimo-button:focus-visible` | — |
| `.eskimo-button:hover` | background-color: #B9F52B |
| `.faq_question:focus-visible` | — |
| `.faq_question:hover` | color: #111313 |
| `.features_tab:active` | transform: scale(0.97) |
| `.features_tab:focus-visible` | — |
| `.features_tab:hover` | color: #111313 |
| `.footer_input:focus` | — |
| `.footer_legal-link:focus-visible` | — |
| `.footer_legal-link:hover` | color: #FFFFFF |
| `.footer_link:focus-visible` | — |
| `.footer_link:hover` | color: #FFFFFF |
| `.highlights_card:hover` | box-shadow: 0 0.75rem 2rem rgba(17, 19, 19, 0.06) |
| `.inaction_play:active` | transform: translateX(-50%) scale(0.96) |
| `.inaction_play:focus-visible` | — |
| `.inaction_play:hover` | transform: translateX(-50%) scale(1.08); filter: brightness(1.05) |
| `.link-read-more:active` | transform: translateY(0.0625rem) |
| `.link-read-more:focus-visible` | — |
| `.link-read-more:hover` | gap: 0.75rem; color: #0875E1 |
| `.nav_link:active` | color: #B9D8FA |
| `.nav_link:focus-visible` | — |
| `.nav_link:hover` | color: #DDEEFF |
| `.nav_login:active` | color: #B9D8FA |
| `.nav_login:focus-visible` | — |
| `.nav_login:hover` | color: #DDEEFF |
| `.nav_menu-button:active` | — |
| `.nav_menu-button:focus-visible` | — |
| `.nav_menu-button:hover` | — |
| `.stories_card:hover` | background-color: #2E92F2; transform: translateY(-0.25rem) |
| `.who_card:hover` | transform: translateY(-0.25rem); box-shadow: 0 0.75rem 2rem rgba(17, 19, 19, 0.08) |

## What the Flowboard → Webflow paste changes

Measured against the exported home page (`eskimo-f95b9c.webflow.css` + `index.html`).
Cosmetic reformatting — `0.2s ease` → `.2s`, `rgba()` → 8-digit hex, dropped
redundant shorthand values — is lossless and ignored here.

| What | Behaviour | Handled by |
|---|---|---|
| `font-family` | **Stripped from every selector.** The Google Fonts `<link>` survives, so the font loads but nothing uses it. | `WEBFLOW-PASTE-REPAIRS.css` §1 — one `body` rule plus form controls |
| `filter: drop-shadow()` | Stripped; kept only as an unused `--fb-preserved-filter`. Substituted with `.box-transform { box-shadow }`, which draws a rectangle behind transparent PNGs. | §2 |
| `aspect-ratio` | Stripped from class styles, re-added automatically in the supplemental embed. No action needed. | — |
| `list-style` | Same: stripped, re-added in the embed. | — |
| `<br class="...">` | Rewritten as `<div class="section-hero-text">`, so authored line breaks become permanent at every breakpoint. | §5 |
| `<button>` | Rewritten as `<a href="#">`. Webflow's own scroll module preventDefaults these, so click handlers still work. Add `role="button"` for a11y. | — |
| `alt` text | **Stripped from every image.** Must be re-entered in the Designer. | manual |
| Webflow base styles | `blockquote` keeps `padding: 10px 20px`; `.w-form` adds `margin-bottom: 15px`. | §3, §4 |
| Tiny icons | 2–4.5px icons were bumped to `0.5rem`. Keep 0.5rem as the floor for chevrons and carets. | adopted going forward |

## Features page — what the paste adds

Rebuilt against the live project rather than against page 01's source, so the
`eskimo-` namespace is retired: the home-page paste kept every Client-First
name intact, so those classes now exist in Webflow with these exact values and
must be reused, not duplicated.

The paste is split into four blocks. Only block D reaches Webflow:

| Block | Contents | On import |
|---|---|---|
| A | preview reset + font | delete |
| B | site-wide repairs (font, drop-shadow, blockquote, `.w-form`, mobile line breaks) | move to Site Settings → Custom Code |
| C | 190 rules generated from `eskimo-f95b9c.webflow.css`, verified byte-identical | skip |
| D | 44 new selectors — none of which collide | paste |

New combo modifiers on existing bases: `.padding-section-large` × `is-hero-sub`,
`is-highlights`, `is-tools`, `is-integrations-tall`, `is-stories-compact`;
`.hero_content/.hero_heading-wrapper/.hero_subheading-wrapper/.hero_visual` ×
`is-sub`; `.tag_icon` × `is-people`, `is-play`; `.collage_item` × eight `is-lm-*`.

New component classes: `.section_highlights`, `.highlights_*` (5),
`.features_grid` + `.features_item-*` (5), `.inaction_*` (8).
