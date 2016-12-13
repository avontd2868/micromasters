// @flow
import React from 'react';

export default class SupportRequestForm extends React.Component {
  props: {
    onClose: Function,
  }
  render() {
    const { onClose } = this.props;
    return (
      <div className="support-request-form">
        <h1>Need some help?</h1>
        <label>Please describe your problem.
          <textarea />
        </label>
        <button className="submit-button">Submit</button>
        <button className="close-button" onClick={onClose}
          aria-label="close">✖
        </button>
      </div>
    );
  }
}
