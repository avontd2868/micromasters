// @flow
import React from 'react';
import { shallow } from 'enzyme';
import moment from 'moment';
import { assert } from 'chai';
import _ from 'lodash';
import sinon from 'sinon';

import CourseListCard from './CourseListCard';
import CourseRow from './CourseRow';
import { DASHBOARD_RESPONSE, COURSE_PRICES_RESPONSE } from '../../constants';

describe('CourseListCard', () => {
  let program, checkout, sandbox;
  beforeEach(() => {
    program = _.cloneDeep(DASHBOARD_RESPONSE[1]);
    assert(program.courses.length > 0);
    sandbox = sinon.sandbox.create();
    checkout = sandbox.stub();
  });

  afterEach(() => {
    sandbox.restore();
  });

  let renderCourseListCard = (props = {}) => {
    let coursePrice = COURSE_PRICES_RESPONSE.find(
      coursePrice => coursePrice.program_id === program.id
    );

    return shallow(
      <CourseListCard
        program={program}
        coursePrice={coursePrice}
        checkout={checkout}
        addCourseEnrollment={() => undefined}
        {...props}
      />
    );
  };

  it('creates a CourseRow for each course', () => {
    let now = moment();
    const wrapper = renderCourseListCard({
      now: now
    });
    assert.equal(wrapper.find(CourseRow).length, program.courses.length);
    let courses = _.sortBy(program.courses, 'position_in_program');
    wrapper.find(CourseRow).forEach((courseRow, i) => {
      const props = courseRow.props();
      assert.equal(props.now, now);
      assert.deepEqual(props.course, courses[i]);
      assert.equal(props.checkout, checkout);
    });
  });

  it("fills in now if it's missing in the props", () => {
    const wrapper = renderCourseListCard();
    let nows = wrapper.find(CourseRow).map(courseRow => courseRow.props().now);
    assert.isAbove(nows.length, 0);
    for (let now of nows) {
      // Each now must be exactly the same object
      assert.equal(now, nows[0]);
    }
  });

  it("doesn't show the personalized pricing box for programs without it", () => {
    program.financial_aid_availability = false;
    const wrapper = renderCourseListCard();
    assert.equal(wrapper.find('.personalized-pricing').length, 0);
  });
});
