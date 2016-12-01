/* global SETTINGS: false, CURRENT_PAGE_URL: false */
__webpack_public_path__ = `http://${SETTINGS.host}:8078/`;  // eslint-disable-line no-undef, camelcase
import "rrssb/js/rrssb.js";

/**
 * Set social media sharing links
 */
jQuery(document).ready(function ($) {
  var description = 'MicroMasters is a ' +
    'new digital credential for online learners. The MicroMasters ' +
    'credential will be granted to learners who complete an ' +
    'integrated set of graduate-level online courses. With the MicroMasters ' +
    "credentials, learners can apply for an accelerated master's degree " +
    "program on campus, at MIT or other top universities.";

  $('.rrssb-buttons').rrssb({
    // required:
    title: 'MITx MicroMasters',
    url: CURRENT_PAGE_URL,

    // optional:
    description: description,
    emailBody: description + CURRENT_PAGE_URL
  });
});
