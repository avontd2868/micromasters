__webpack_public_path__ = `http://${SETTINGS.host}:8078/`;  // eslint-disable-line no-undef, camelcase

// jquery imported here since style_public.js is loaded before public.js
import $ from 'jquery';
window.jQuery = $;
window.$ = $;

import "style-loader!css-loader!../../scss/public_style/web-icons.css";
import "style-loader!css-loader!../../scss/public_style/bootstrap-extend.css";
import "style-loader!css-loader!rrssb/css/rrssb.css";
