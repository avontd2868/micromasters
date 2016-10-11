/* global SETTINGS: false */
// @flow
import React from 'react';
import { shallow } from 'enzyme';
import moment from 'moment';
import { assert } from 'chai';
import sinon from 'sinon';
import _ from 'lodash';

import CourseAction from './CourseAction';
import {
  DASHBOARD_FORMAT,
  COURSE_PRICES_RESPONSE,
  FINANCIAL_AID_PARTIAL_RESPONSE,
  STATUS_PASSED,
  STATUS_NOT_PASSED,
  STATUS_OFFERED,
  STATUS_CAN_UPGRADE,
  STATUS_CURRENTLY_ENROLLED,
  STATUS_WILL_ATTEND,
  FA_PENDING_STATUSES,
  FA_STATUS_SKIPPED
} from '../../constants';
import { findCourse, findAndCloneCourse } from '../../util/test_utils';

describe('CourseAction', () => {
  const now = moment();
  let sandbox, checkoutStub, coursePrice, defaultParams, defaultParamsNow;

  beforeEach(() => {
    sandbox = sinon.sandbox.create();
    checkoutStub = sandbox.stub();
    coursePrice = COURSE_PRICES_RESPONSE[1];
    defaultParams = {
      checkout: checkoutStub,
      coursePrice: coursePrice,
      hasFinancialAid: false,
      financialAid: {},
      addCourseEnrollment: sandbox.stub(),
    };
    defaultParamsNow = Object.assign({}, defaultParams, { now: now });
  });

  afterEach(() => {
    sandbox.restore();
  });

  let getElements = (renderedComponent) => {
    let button = renderedComponent.find(".dashboard-button");
    let buttonText;
    if (button.length > 0 && button.children().length > 0) {
      buttonText = button.children().text();
    }
    let description = renderedComponent.find(".description");
    let descriptionText = description.length === 1 ? description.text() : undefined;
    let link = renderedComponent.find("a");
    let linkText = link.length === 1 ? link.text() : undefined;
    return {
      button: button,
      buttonText: buttonText,
      descriptionText: descriptionText,
      linkText: linkText
    };
  };

  let alterFirstRun = (course, overrideObject) => {
    course.runs[0] = Object.assign({}, course.runs[0], overrideObject);
  };

  let assertCheckoutButton = (button, courseId) => {
    button.simulate('click');
    assert.isAbove(checkoutStub.callCount, 0);
    assert.deepEqual(checkoutStub.args[0], [courseId]);
  };

  it('shows passed for a passed course', () => {
    let course = findCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_PASSED
    ));
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    assert.equal(wrapper.find(".passed").text(), 'Passed');
  });

  it('shows nothing for a failed course', () => {
    let course = findCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_NOT_PASSED
    ));
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    assert.equal(wrapper.text(), '');
  });

  it('shows a message for a verified course', () => {
    let course = findCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_CURRENTLY_ENROLLED
    ));
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    let elements = getElements(wrapper);

    assert.equal(elements.descriptionText, 'In Progress');
  });

  it('shows a button to enroll and pay, and a link to enroll and pay later', () => {
    let course = findCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_OFFERED
    ));
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    let firstRun = course.runs[0];
    let elements = getElements(wrapper);

    assert.isUndefined(elements.button.props().disabled);
    assert.include(elements.buttonText, 'Pay Now');
    assert.equal(elements.linkText, 'Enroll and pay later');
    assertCheckoutButton(elements.button, firstRun.course_id);
  });

  it('shows an enroll button if user is not enrolled and enrollment starts today or earlier', () => {
    let course = findAndCloneCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_OFFERED &&
      course.runs[0].enrollment_start_date !== undefined
    ));
    let nowString = now.toISOString();
    let pastString = moment(now).add(-10, 'days').toISOString();

    [nowString, pastString].forEach(dateString => {
      alterFirstRun(course, {enrollment_start_date: dateString});
      const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
      let firstRun = course.runs[0];
      let elements = getElements(wrapper);

      assert.isUndefined(elements.button.props().disabled);
      assert.include(elements.buttonText, 'Pay Now');
      assert.equal(elements.linkText, 'Enroll and pay later');
      assertCheckoutButton(elements.button, firstRun.course_id);
    });
  });

  it('shows an upgrade button if user is not verified but is enrolled', () => {
    let course = findCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_CAN_UPGRADE
    ));
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    let firstRun = course.runs[0];
    let elements = getElements(wrapper);
    let formattedUpgradeDate = moment(firstRun.course_upgrade_deadline).format(DASHBOARD_FORMAT);

    assert.isUndefined(elements.button.props().disabled);
    assert.include(elements.buttonText, 'Pay Now');
    assert.equal(elements.descriptionText, `Payment due: ${formattedUpgradeDate}`);
    assertCheckoutButton(elements.button, firstRun.course_id);
  });

  it('shows a message if a user is not enrolled and the course has a future enrollment start date', () => {
    let course = findAndCloneCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_OFFERED
    ));
    let enrollmentStartDate = moment(now).add(10, 'days').toISOString();
    alterFirstRun(course, {enrollment_start_date: enrollmentStartDate});
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    let firstRun = course.runs[0];
    let elements = getElements(wrapper);

    assert.equal(elements.button.length, 0);
    let formattedDate = moment(firstRun.enrollment_start_date).format(DASHBOARD_FORMAT);
    assert.equal(elements.descriptionText, `Enrollment begins ${formattedDate}`);
  });

  it('shows a message if a user is not enrolled and the course has a fuzzy enrollment date', () => {
    let course = findAndCloneCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_OFFERED
    ));
    alterFirstRun(course, {
      fuzzy_enrollment_start_date: 'whenever',
      enrollment_start_date: null
    });
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    let elements = getElements(wrapper);

    assert.equal(elements.button.length, 0);
    assert.equal(elements.descriptionText, 'Enrollment begins whenever');
  });

  it('shows a countdown message if the user is enrolled and the course starts in the future', () => {
    let course = findCourse(course => (
      course.runs.length > 0 &&
      course.runs[0].status === STATUS_WILL_ATTEND
    ));
    let startDate = moment(now).add(10, 'days').toISOString();
    alterFirstRun(course, {course_start_date: startDate});
    const wrapper = shallow(<CourseAction course={course} {...defaultParamsNow} />);
    let elements = getElements(wrapper);

    assert.include(elements.descriptionText, 'Course starts in 10 days');
  });

  describe('with financial aid', () => {
    let course, aidParams;

    beforeEach(() => {
      course = findAndCloneCourse(course => (
        course.runs.length > 0 &&
        course.runs[0].status === STATUS_OFFERED
      ));
      aidParams = Object.assign({}, {
        financialAid: _.cloneDeep(FINANCIAL_AID_PARTIAL_RESPONSE),
        hasFinancialAid: true
      });
    });

    it('indicates that a user must calculate the course price', () => {
      alterFirstRun(course, {
        enrollment_start_date: now.toISOString(),
      });
      aidParams.financialAid.has_user_applied = false;

      let params = Object.assign({}, defaultParamsNow, aidParams);
      const wrapper = shallow(
        <CourseAction course={course} {...params} />
      );
      let elements = getElements(wrapper);

      assert.isUndefined(elements.button.props().disabled);
      assert.equal(elements.buttonText, 'Calculate Cost');
      assert.equal(elements.linkText, 'Enroll and pay later');
    });

    it('shows an enroll/pay button if a user has skipped financial aid', () => {
      alterFirstRun(course, {
        enrollment_start_date: now.toISOString(),
      });
      aidParams.financialAid.has_user_applied = false;
      aidParams.financialAid.application_status = FA_STATUS_SKIPPED;

      let params = Object.assign({}, defaultParamsNow, aidParams);
      const wrapper = shallow(
        <CourseAction course={course} {...params} />
      );
      let elements = getElements(wrapper);

      assert.isUndefined(elements.button.props().disabled);
      assert.include(elements.buttonText, 'Pay Now');
      assert.equal(elements.linkText, 'Enroll and pay later');
    });

    it('shows a disabled enroll/pay button if a user is pending approval', () => {
      alterFirstRun(course, {
        enrollment_start_date: now.toISOString(),
      });
      aidParams.financialAid.has_user_applied = true;

      FA_PENDING_STATUSES.forEach(pendingStatus => {
        aidParams.financialAid.application_status = pendingStatus;

        let params = Object.assign({}, defaultParamsNow, aidParams);
        const wrapper = shallow(
          <CourseAction course={course} {...params} />
        );
        let elements = getElements(wrapper);

        assert.isTrue(elements.button.props().disabled);
        assert.include(elements.buttonText, 'Pay Now');
        assert.equal(elements.linkText, 'Enroll and pay later');
      });
    });
  });
});
