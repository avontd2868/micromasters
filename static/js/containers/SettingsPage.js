// @flow
/* global SETTINGS: false */
import React from 'react';
import { connect } from 'react-redux';
import Loader from '../components/Loader';

import { startProfileEdit } from '../actions/profile';
import { FETCH_PROCESSING } from '../actions/index';
import ProfileFormContainer from './ProfileFormContainer';
import PrivacyForm from '../components/PrivacyForm';
import ProfileProgressControls from '../components/ProfileProgressControls';
import { privacyValidation } from '../lib/validation/profile';

class SettingsPage extends ProfileFormContainer {
  componentWillMount() {
    this.startSettingsEdit();
  }

  startSettingsEdit() {
    const { dispatch } = this.props;
    dispatch(startProfileEdit(SETTINGS.user.username));
  }

  render() {
    const { profiles } = this.props;
    let props = this.profileProps(profiles[SETTINGS.user.username]);
    let loaded = false;
    const username = SETTINGS.user.username;

    if (profiles[username] !== undefined) {
      let profileFromStore = profiles[username];
      loaded = profileFromStore.getStatus !== FETCH_PROCESSING;
    }

    return (
      <Loader loaded={loaded}>
        <div className="single-column privacy-form">
          <h4 className="privacy-form-heading">Settings</h4>
          <PrivacyForm {...props} validator={privacyValidation} />
          <ProfileProgressControls
            {...props}
            nextBtnLabel="Save"
            nextUrl="/dashboard"
            isLastTab={true}
            validator={privacyValidation}
          />
        </div>
      </Loader>
    );
  }
}

export default connect(ProfileFormContainer.mapStateToProps)(SettingsPage);
