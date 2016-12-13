/* global SETTINGS:false zE:false _:false */
__webpack_public_path__ = `http://${SETTINGS.host}:8078/`;  // eslint-disable-line no-undef, camelcase

import React from 'react';
import ReactDOM from 'react-dom';
import SupportRequest from '../components/SupportRequest';

document.addEventListener("DOMContentLoaded", () => {
  const mount = document.createElement("div");
  mount.id = "support-request";
  document.body.appendChild(mount);

  ReactDOM.render(
    <SupportRequest />,
    mount
  );
});
