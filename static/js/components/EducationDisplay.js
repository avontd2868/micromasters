import React from 'react';
import IconButton from 'react-mdl/lib/IconButton';

import Grid, { Cell } from 'react-mdl/lib/Grid';
import FABButton from 'react-mdl/lib/FABButton';
import Icon from 'react-mdl/lib/Icon';
import { Card } from 'react-mdl/lib/Card';
import Menu from 'react-mdl/lib/Menu';
import { MenuItem } from 'react-mdl/lib/Menu';
import _ from 'lodash';
import moment from 'moment';

import ProfileFormFields from '../util/ProfileFormFields';
import ConfirmDeletion from './ConfirmDeletion';
import EducationDialog from './EducationDialog';
import {
  openEditEducationForm,
  openNewEducationForm,
  deleteEducationEntry,
} from '../util/editEducation';
import { userPrivilegeCheck } from '../util/util';

export default class EducationDisplay extends ProfileFormFields {
  openEditEducationForm = index => {
    openEditEducationForm.call(this, index);
  }

  openNewEducationForm = (level, index) => {
    openNewEducationForm.call(this, level, index);
  };

  deleteEducationEntry = () => {
    deleteEducationEntry.call(this);
  };

  educationRow = (entry, index) => {
    const { profile, errors } = this.props;
    if (!('id' in entry)) {
      // don't show new educations, wait until we saved on the server before showing them
      return;
    }

    let deleteEntry = () => this.openEducationDeleteDialog(index);
    let editEntry = () => this.openEditEducationForm(index);
    let validationAlert = () => {
      if (_.get(errors, ['education', index])) {
        return <IconButton name="error" onClick={editEntry} />;
      }
    };
    let dateFormat = date => moment(date).format("MM[/]YYYY");
    let degree = this.educationLevelOptions.find(level => (
      level.value === entry.degree_name
    )).label;
    let icons = () => (
      <Cell col={2} className="profile-row-icons">
        {validationAlert()}
        <IconButton className="edit-button" name="edit" onClick={editEntry} />
        <IconButton className="delete-button" name="delete" onClick={deleteEntry} />
      </Cell>
    );
    return (
      <Grid className="profile-tab-card-grid user-page" key={index}>
        <Cell col={4} className="profile-row-name">
          <span className="school-type">{ degree }</span><br/>
          { entry.school_name }
        </Cell>
        <Cell col={6} className="profile-row-date-range">
          {`${dateFormat(entry.graduation_date)}`}
        </Cell>
        { userPrivilegeCheck(profile, icons, () => <Cell col={2} />) }
      </Grid>
    );
  };

  addEducationMenu = () => {
    let menuItems = this.educationLevelOptions.map(educationLevel => (
      <MenuItem 
        key={educationLevel.label}
        onClick={() => this.openNewEducationForm(educationLevel.value, null)}>
        { educationLevel.label }
      </MenuItem>
    ));
    return (
      <Menu
        target="add-education-button"
        valign="top"
        align="right"
        className="add-education-menu"
      >
        { menuItems }
      </Menu>
    );
  };

  renderEducationEntries = () => {
    const { profile, profile: { education }} = this.props;
    let rows = [];
    if (education !== undefined) {
      rows = education.map( (entry, index) => this.educationRow(entry, index));
    }
    userPrivilegeCheck(profile, () => {
      rows.push(
        <FABButton
          colored
          id="add-education-button"
          className="profile-add-button"
          key="I'm unique!"
        >
          <Icon name="add" />
        </FABButton>
      );
    });
    return rows;
  }

  render() {
    const {
      profile,
      ui: { showEducationDeleteDialog }
    } = this.props;
    return (
      <div>
        <ConfirmDeletion
          deleteEntry={this.deleteEducationEntry}
          open={showEducationDeleteDialog}
          close={this.closeConfirmDeleteDialog}
        />
        <EducationDialog {...this.props} />
        <Card shadow={1} className="profile-tab-card" id="education-card">
          <Grid className="profile-tab-card-grid">
            <Cell col={4} className="profile-card-title">
              Education
            </Cell>
            <Cell col={8} />
          </Grid>
          { this.renderEducationEntries() }
          { userPrivilegeCheck(profile, this.addEducationMenu(), undefined) }
        </Card>
      </div>
    );
  }
}