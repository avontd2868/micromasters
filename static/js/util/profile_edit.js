// @flow
import React from 'react';
import _ from 'lodash';
import R from 'ramda';
import TextField from 'material-ui/TextField';
import { RadioButton, RadioButtonGroup } from 'material-ui/RadioButton';
import Checkbox from 'material-ui/Checkbox';
import Geosuggest from 'react-geosuggest';

import DateField from '../components/inputs/DateField';
import { validationErrorSelector, classify } from './util';
import type { Validator, UIValidator } from '../lib/validation/profile';
import type { Profile } from '../flow/profileTypes';
import type { Option } from '../flow/generalTypes';

// utility functions for pushing changes to profile forms back to the
// redux store.
// this expects that the `updateProfile` and `profile` props are passed
// in to whatever component it is used in.

/**
 * bind this to this.boundRadioGroupField in the constructor of a form component
 * to update radio buttons.
 * pass in the name (used as placeholder), key for profile, and the options.
 */
const radioStyles = {
  labelStyle: {
    left: -10,
    width: '100%'
  }
};

const radioButtonLabelSelector = label => `radio-label-${classify(label)}`;

const radioButtonLabel = label => (
  <label
    id={radioButtonLabelSelector(label)}
    className="radio-label"
  >
    { label }
  </label>
);

const radioButtons = R.map(option => (
  <RadioButton
    className="profile-radio-button"
    labelStyle={radioStyles.labelStyle}
    value={option.value}
    aria-labelledby={radioButtonLabelSelector(option.label)}
    label={radioButtonLabel(option.label)}
    key={radioButtonLabel(option.label)}
  />
));

export function boundRadioGroupField(keySet: string[], label: string, options: Option[]): React$Element<*> {
  const { profile, updateProfile, errors, validator, updateValidationVisibility } = this.props;
  let onChange = e => {
    let clone = _.cloneDeep(profile);
    let value = e.target.value;
    if (value === "true") {
      value = true;
    } else if (value === "false") {
      value = false;
    }
    _.set(clone, keySet, value);
    updateValidationVisibility(keySet);
    updateProfile(clone, validator);
  };

  const value = String(_.get(profile, keySet));
  return (
    <fieldset className={validationErrorSelector(errors, keySet)}>
      <legend className="profile-radio-group-label">
        {label}
      </legend>
      <RadioButtonGroup
        className="profile-radio-group"
        name={label}
        onChange={onChange}
        valueSelected={value}
      >
        {radioButtons(options)}
      </RadioButtonGroup>
      <span className="validation-error-text">
        {_.get(errors, keySet)}
      </span>
    </fieldset>
  );
}

/**
 * bind to this.boundTextField in the constructor of a form component
 * to update text fields when editing the profile
 * we pass in a keyset looking like this:
 *
 * ["top-level-key", index, "nested_object_key"] or just ["top_level_key"]
 */
export function boundTextField(
  keySet: string[],
  label: string,
  multiLine: boolean=false
): React$Element<*> {
  const {
    profile,
    errors,
    updateProfile,
    validator,
    updateValidationVisibility,
    updateProfileValidation,
  } = this.props;

  let onChange = e => {
    let clone = _.cloneDeep(profile);
    _.set(clone, keySet, e.target.value);
    updateValidationVisibility(keySet);
    updateProfile(clone, validator);
  };

  let onBlur = () => {
    updateValidationVisibility(keySet);
    updateProfileValidation(profile, validator);
  };

  let getValue = () => {
    let value = _.get(profile, keySet, "");
    return ( _.isNull(value) || _.isUndefined(value) ) ? "" : value;
  };

  // fullWidth means set width to 100% instead of 256px. This lets us use the
  // Grid and Cell to manage its size
  return (
    <TextField
      onBlur={onBlur}
      name={label}
      multiLine={multiLine}
      className={validationErrorSelector(errors, keySet)}
      floatingLabelText={label}
      value={getValue()}
      fullWidth={true}
      errorText={_.get(errors, keySet)}
      onChange={onChange} />
  );
}

/**
 * bind this to this.boundDateField in the constructor of a form component
 * to update date fields
 * pass in the name (used as placeholder), key for profile.
 */
export function boundDateField(keySet: string[], label: string, omitDay: boolean, allowFutureYear: boolean = false): React$Element<*> { // eslint-disable-line max-len
  const {
    profile,
    errors,
    updateProfile,
    validator,
    updateValidationVisibility,
    updateProfileValidation,
  } = this.props;

  let onBlur = () => {
    updateValidationVisibility(keySet);
    updateProfileValidation(profile, validator);
  };


  return <DateField
    data={profile}
    errors={errors}
    updateHandler={updateProfile}
    onBlur={onBlur}
    validator={validator}
    keySet={keySet}
    label={label}
    omitDay={omitDay}
    allowFutureYear={allowFutureYear}
  />;
}

export function boundCheckbox(keySet: string[], label: string|React$Element<*>): React$Element<*> {
  const {
    profile,
    errors,
    updateProfile,
    validator,
    updateValidationVisibility,
  } = this.props;

  let onChange = e => {
    let clone = _.cloneDeep(profile);
    _.set(clone, keySet, e.target.checked);
    updateValidationVisibility(keySet);
    updateProfile(clone, validator);
  };

  const style = {
    'backgroundColor': '#a31f34'
  };

  return (
    <div className={`bound-check-box ${validationErrorSelector(errors, keySet)}`}>
      <div className="first-row">
        <Checkbox
          checked={_.get(profile, keySet)}
          onCheck={onChange}
          inputStyle={style}
        />
        <span className="label">
          { label }
        </span>
      </div>
      <span className="validation-error-text">
        {_.get(errors, keySet)}
      </span>
    </div>
  );
}


export function boundGeosuggest(keySet: string[], label: string|React$Element<*>,
  { id, placeholder, types }: { id: string, placeholder: string, types: string[] } = {}
): React$Element<*> {
  const {
    profile,
    errors,
    updateProfile,
    validator,
    updateValidationVisibility,
  } = this.props;

  const addressComponentTypeMap = {
    // From the name that we use, to the component type that Google Maps uses.
    // See https://developers.google.com/maps/documentation/geocoding/intro#Types
    "city": "locality",
    "state_or_territory": "administrative_area_level_1",
    "country": "country",
  };

  const onSuggestSelect = (suggest) => {
    if (!suggest || !suggest.gmaps) {
      return;
    }
    const components = suggest.gmaps.address_components;
    let clone = _.cloneDeep(profile);
    keySet.forEach((key) => {
      const gmapType = addressComponentTypeMap[key];
      const component = _.find(components, (c) => _.includes(c.types, gmapType));
      clone[key] = component.long_name;
    });
    updateValidationVisibility(keySet);
    updateProfile(clone, validator);
  };

  const onBlur = (value) => {
    if (!value) {
      let clone = _.cloneDeep(profile);
      keySet.forEach((key) => {
        clone[key] = null;
      });
      updateValidationVisibility(keySet);
      updateProfile(clone, validator);
    }
  }

  const hasValue = R.and(
    R.compose(R.not, R.isEmpty),
    R.compose(R.not, R.isNil),
  );
  const hasKeySetProps = R.allPass(R.map(R.has, keySet));

  const hasExistingAddress = R.allPass([
    hasValue,
    hasKeySetProps,
    R.compose(R.all(hasValue), R.props(keySet)),
  ]);

  const formatInitialAddress = R.ifElse(
    hasExistingAddress,
    R.compose(R.join(", "), R.props(keySet)),
    R.always(""),
  )

  const initial = formatInitialAddress(profile);

  return (
    <div>
      <Geosuggest initialValue={initial}
        id={id} label={label} placeholder={placeholder} types={types}
        onSuggestSelect={onSuggestSelect} onBlur={onBlur}
      />
      <span className="validation-error-text">
        {_.get(errors, keySet)}
      </span>
    </div>
  );
}

/**
 * Validates the profile then PATCHes the profile if validation succeeded.
 * Returns a promise which resolves with the new profile if validation and PATCH succeeded,
 * or rejects if either failed
 */
export function saveProfileStep(validator: Validator|UIValidator, isLastStep: boolean = false): Promise<Profile> {
  const { saveProfile, profile, ui } = this.props;
  let clone = {
    ...profile,
    filled_out: profile.filled_out || isLastStep
  };

  if (isLastStep && !profile.filled_out) {
    clone.email_optin = true;
  }
  return saveProfile(validator, clone, ui);
}
