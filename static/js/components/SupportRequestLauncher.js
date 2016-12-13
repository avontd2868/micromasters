// @flow
import React from 'react';
import { FABButton, Icon } from 'react-mdl';

export default class SupportRequestLauncher extends React.Component {
  props: {
    onClick: Function,
  }
  render() {
    const { onClick } = this.props;
    return (
      <FABButton className="support-request-launcher"
        onClick={onClick}>
        <Icon name="help_outline" />
      </FABButton>
    );
  }
}
