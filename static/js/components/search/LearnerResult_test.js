// @flow
/* global SETTINGS: false */
import React from 'react';
import { assert } from 'chai';
import { shallow } from 'enzyme';

import ProfileImage from '../../containers/ProfileImage';
import LearnerResult from './LearnerResult';
import {
  getUserDisplayName,
} from '../../util/util';
import {
  USER_PROFILE_RESPONSE,
  USER_PROGRAM_RESPONSE
} from '../../constants';

describe('LearnerResult', () => {
  let renderLearnerResult = (props = {}) => shallow(
    <LearnerResult
      result={{
        _source: {
          profile: USER_PROFILE_RESPONSE,
          program: USER_PROGRAM_RESPONSE,
        }
      }}
      {...props}
    />
  );

  it("should include the user's name", () => {
    let result = renderLearnerResult().find(".learner-name").find("span");
    assert.include(result.text(), getUserDisplayName(USER_PROFILE_RESPONSE));
  });

  it("should include the user's location", () => {
    let result = renderLearnerResult().find(".learner-location").find("span");
    assert.include(result.text(), USER_PROFILE_RESPONSE.city);
    assert.include(result.text(), USER_PROFILE_RESPONSE.country);
  });

  it("should include the user's current program grade when a grade is available", () => {
    let result = renderLearnerResult().find(".learner-grade .percent");
    assert.include(result.text(), `${USER_PROGRAM_RESPONSE.grade_average}%`);
  });

  it("should show an indicator when a user has a missing/null program grade", () => {
    let emptyGradeElasticHit = {
      _source: {
        profile: USER_PROFILE_RESPONSE,
        program: {
          ...USER_PROGRAM_RESPONSE,
          grade_average: null,
        }
      }
    };
    let result = renderLearnerResult({result: emptyGradeElasticHit}).find(".learner-grade .percent");
    assert.equal(result.text(), "-");
    delete emptyGradeElasticHit._source.program.grade_average;
    result = renderLearnerResult({result: emptyGradeElasticHit}).find('.learner-grade .percent');
    assert.equal(result.text(), "-");
  });

  it('should use the small avatar', () => {
    let result = renderLearnerResult();
    assert.isTrue(result.find(ProfileImage).props().useSmall);
  });
});
