// @flow
import React from 'react';
import SupportRequestLauncher from './SupportRequestLauncher';
import SupportRequestForm from './SupportRequestForm';

export default class SupportRequest extends React.Component {
  state = {
    isActive: false
  }
  activate = () => {
    this.setState({isActive: true});
  }
  deactivate = () => {
    this.setState({isActive: false});
  }
  render() {
    const { isActive } = this.state;
    if (isActive) {
      return <SupportRequestForm onClose={this.deactivate} />;
    } else {
      return <SupportRequestLauncher onClick={this.activate} />;
    }
  }
}
