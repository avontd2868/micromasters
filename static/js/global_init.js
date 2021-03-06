// Define globals we would usually get from Django
const _createSettings = () => ({
  user: {
    username: "jane",
    email: "jane@example.com",
    first_name: "Jane",
    last_name: "Doe",
    preferred_name: "JD"
  },
  edx_base_url: "/edx/",
  roles: [],
  support_email: "a_real_email@example.com",
  es_page_size: 40,
  get username() {
    throw new Error("username was removed");
  }
});

global.SETTINGS = _createSettings();

// polyfill for Object.entries
import entries from 'object.entries';
if (!Object.entries) {
  entries.shim();
}

// Make sure window and document are available for testing
require('jsdom-global')();

// cleanup after each test run
afterEach(function (){
  document.body.innerHTML = '';
  global.SETTINGS = _createSettings();
});

// required for interacting with react-mdl components
require('react-mdl/extra/material.js');

// rethrow all unhandled promise errors
process.on('unhandledRejection', reason => { // eslint-disable-line no-unused-vars
  // throw reason; // uncomment to show promise-related errors
});

// fix 'unknown prop' error
import injectTapEventPlugin from 'react-tap-event-plugin';
injectTapEventPlugin();

// enable chai-as-promised
import chai from 'chai';
import chaiAsPromised from 'chai-as-promised';
chai.use(chaiAsPromised);
